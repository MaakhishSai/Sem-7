#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <cuda_runtime.h>

// Error checking macro for CUDA calls
#define check_cuda(call) do {                                   \
    cudaError_t _e = (call);                                    \
    if (_e != cudaSuccess) {                                    \
        fprintf(stderr, "cuda error %s:%d: %s\n",               \
                __FILE__, __LINE__, cudaGetErrorString(_e));    \
        exit(EXIT_FAILURE);                                     \
    }                                                           \
} while(0)

// To ensure that even the smallest errors are handled
#define eps_pivot 1e-18

// Performance metrics structure for the timing data
typedef struct {
    long long total_flops;
    long long total_mem_acc;
    double cgma;
    long long total_thread_calls;
    int blocks_per_grid;
    int threads_per_block;
} performance_metrics;

// Calculate performance metrics using same heuristics as sample  
void cal_metrics(int n, performance_metrics *pm) {
    long long nlong = (long long)n;
    pm->total_flops = (2 * nlong * nlong * nlong) / 3 + 2 * nlong * nlong;
    pm->total_mem_acc = 5 * nlong * nlong + 2 * nlong;
    pm->cgma = (double)pm->total_flops / (double)pm->total_mem_acc;

    long long total_threads = 0;
    for (int k = 0; k < n - 1; ++k) {
        total_threads += (n - k); 
        total_threads += n / 2;
        total_threads += (n - k - 1);  
        long long s = (long long)(n - k - 1);
        total_threads += s * s;
    }  
    total_threads += n + n;
    pm->total_thread_calls = total_threads;

    long long peak_threads = (long long)(n - 1) * (long long)(n - 1);
    pm->threads_per_block = 256;
    pm->blocks_per_grid = (int)((peak_threads + pm->threads_per_block - 1) / pm->threads_per_block);
}

// Kernels  

// Per-block max abs value in column k
__global__ void block_max_kernel(const double *ad_a, double *ad_blk_val, int *ad_blk_idx, int n, int k, int rows_to_check) {
    extern __shared__ double sdata[]; // blockDim.x doubles then blockDim.x ints  
    double *sval = sdata;
    int *sidx = (int*)(sdata + blockDim.x);

    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x + tid;

    double local_val = -1.0;
    int local_idx = k;

    if (gid < rows_to_check) {
        int row = k + gid;
        double v = ad_a[row * n + k];
        local_val = fabs(v);
        local_idx = row;
    }
    sval[tid] = local_val;
    sidx[tid] = local_idx;
    __syncthreads();

    for (int stride = blockDim.x >> 1; stride > 0; stride >>= 1) {
        if (tid < stride) {
            if (sval[tid + stride] > sval[tid]) {
                sval[tid] = sval[tid + stride];
                sidx[tid] = sidx[tid + stride];
            }
        }
        __syncthreads();
    }

    if (tid == 0) {
        ad_blk_val[blockIdx.x] = sval[0];
        ad_blk_idx[blockIdx.x] = sidx[0];
    }
}

// Swap first 'cols' columns of rows r1 and r2 in ad_mat  
__global__ void row_swap_kernel(double *ad_mat, int n, int r1, int r2, int cols) {
    int c = blockIdx.x * blockDim.x + threadIdx.x;
    if (c < cols) {
        double t = ad_mat[r1 * n + c];
        ad_mat[r1 * n + c] = ad_mat[r2 * n + c];
        ad_mat[r2 * n + c] = t;
    }
}

// Swap two entries in a vector 
__global__ void vec_swap_kernel(double *ad_vec, int i, int j) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        double t = ad_vec[i];
        ad_vec[i] = ad_vec[j];
        ad_vec[j] = t;
    }
}

// Compute L's multipliers: L[i,k] = A[i,k] / A[k,k] for i>k  
__global__ void compute_factors_kernel(const double *ad_a, double *ad_l, int n, int k) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    int row = k + 1 + tid;
    if (row < n) {
        double pivot = ad_a[k * n + k];
        if (fabs(pivot) > eps_pivot) {
            ad_l[row * n + k] = ad_a[row * n + k] / pivot;
        } else {
            ad_l[row * n + k] = 0.0;
        }
    }
}

// A[i,j] -= L[i,k] * A[k,j] using tile of size blockDim.y x blockDim.x  
__global__ void subMat_kernel(double *ad_a, const double *ad_l, int n, int k)
{
    extern __shared__ double sblock[];  
    double *sL = sblock;
    double *sU = sblock + blockDim.y;

    int local_row = threadIdx.y;
    int local_col = threadIdx.x;
    int global_row = k + 1 + blockIdx.y * blockDim.y + local_row;
    int global_col = k + 1 + blockIdx.x * blockDim.x + local_col;

    if (local_col == 0) {
        if (global_row < n) sL[local_row] = ad_l[global_row * n + k];
        else sL[local_row] = 0.0;
    }
    if (local_row == 0) {
        if (global_col < n) sU[local_col] = ad_a[k * n + global_col];
        else sU[local_col] = 0.0;
    }
    __syncthreads();

    if (global_row < n && global_col < n) {
        double lik = sL[local_row];
        double ukj = sU[local_col];
        ad_a[global_row * n + global_col] -= lik * ukj;
    }
}

void read_input(const char *fname, int *ah_n, double **ah_a, double **ah_b, double *ah_read_time_ms) {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    FILE *f = fopen(fname, "r");
    if (!f) { perror("fopen"); exit(EXIT_FAILURE); }
    if (fscanf(f, "%d", ah_n) != 1) { fprintf(stderr, "bad input\n"); exit(EXIT_FAILURE); }
    int n = *ah_n;
    size_t mat_bytes = (size_t)n * n * sizeof(double);
    *ah_a = (double*) malloc(mat_bytes);
    *ah_b = (double*) malloc((size_t)n * sizeof(double));
    if (!*ah_a || !*ah_b) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }

    for (int i = 0; i < n * n; ++i) {
        if (fscanf(f, "%lf", &((*ah_a)[i])) != 1) { fprintf(stderr, "bad a\n"); exit(EXIT_FAILURE); }
    }
    for (int i = 0; i < n; ++i) {
        if (fscanf(f, "%lf", &((*ah_b)[i])) != 1) { fprintf(stderr, "bad b\n"); exit(EXIT_FAILURE); }
    }
    fclose(f);

    clock_gettime(CLOCK_MONOTONIC, &t1);
    *ah_read_time_ms = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
}
  
void write_output(const char *fname, int n, const double *ah_l, const double *ah_u, const double *ah_x) {
    FILE *f = fopen(fname, "w");
    if (!f) { perror("fopen"); exit(EXIT_FAILURE); }
    fprintf(f, "%d\n", n);
    for (int i = 0; i < n * n; ++i) fprintf(f, "%.16e\n", ah_l[i]);
    for (int i = 0; i < n * n; ++i) fprintf(f, "%.16e\n", ah_u[i]);
    for (int i = 0; i < n; ++i) fprintf(f, "%.16e\n", ah_x[i]);
    fclose(f);
}
  
void host_solve(int n, const double *ah_l, const double *ah_u, const double *ah_b_perm, double *ah_x) {
    double *ah_y = (double*) malloc((size_t)n * sizeof(double));
    if (!ah_y) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }

    for (int i = 0; i < n; ++i) {
        double s = 0.0;
        for (int j = 0; j < i; ++j) s += ah_l[i * n + j] * ah_y[j];
        ah_y[i] = ah_b_perm[i] - s;
    }
    for (int i = n - 1; i >= 0; --i) {
        double s = 0.0;
        for (int j = i + 1; j < n; ++j) s += ah_u[i * n + j] * ah_x[j];
        double d = ah_u[i * n + i];
        if (fabs(d) < eps_pivot) {
            fprintf(stderr, "warning: small diag u[%d]=%e\n", i, d);
            ah_x[i] = 0.0;
        } else {
            ah_x[i] = (ah_y[i] - s) / d;
        }
    }
    free(ah_y);
}
 
void gpu_lup_factorize(int n, double *ad_a, double *ad_l, double *ad_b, float *gpu_L_time_ms_out, float *gpu_U_time_ms_out) {
    const int block1d = 256;
    const int tile = 16;

    int max_blocks = (n + block1d - 1) / block1d;
    double *ad_blk_val = NULL;
    int *ad_blk_idx = NULL;
    check_cuda(cudaMalloc((void**)&ad_blk_val, sizeof(double) * max_blocks));
    check_cuda(cudaMalloc((void**)&ad_blk_idx,  sizeof(int)    * max_blocks));

    double *ah_blk_val = (double*) malloc(sizeof(double) * max_blocks);
    int *ah_blk_idx = (int*) malloc(sizeof(int) * max_blocks);
    if (!ah_blk_val || !ah_blk_idx) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }

    // events for L and U timing
    cudaEvent_t ev_l_s, ev_l_e, ev_u_s, ev_u_e;
    check_cuda(cudaEventCreate(&ev_l_s)); check_cuda(cudaEventCreate(&ev_l_e));
    check_cuda(cudaEventCreate(&ev_u_s)); check_cuda(cudaEventCreate(&ev_u_e));
    float sum_l_ms = 0.0f;
    float sum_u_ms = 0.0f;

    for (int k = 0; k < n - 1; ++k) {
        int rows_to_check = n - k;
        int blocks = (rows_to_check + block1d - 1) / block1d;

        // stage1: per-block local max  
        size_t shmem = (size_t)block1d * sizeof(double) + (size_t)block1d * sizeof(int);
        block_max_kernel<<<blocks, block1d, shmem>>>(ad_a, ad_blk_val, ad_blk_idx, n, k, rows_to_check);
        check_cuda(cudaGetLastError());
        check_cuda(cudaDeviceSynchronize());

        // copy per-block results and reduce on host  
        check_cuda(cudaMemcpy(ah_blk_val, ad_blk_val, sizeof(double) * blocks, cudaMemcpyDeviceToHost));
        check_cuda(cudaMemcpy(ah_blk_idx, ad_blk_idx, sizeof(int) * blocks, cudaMemcpyDeviceToHost));
        double best = -1.0; int pivot_row = k;
        for (int b = 0; b < blocks; ++b) {
            if (ah_blk_val[b] > best) { best = ah_blk_val[b]; pivot_row = ah_blk_idx[b]; }
        }
        if (best < eps_pivot) {
            fprintf(stderr, "Warning: pivot almost near zero at k=%d (best=%e)\n", k, best);
        }

        // Swap only if needed: ad_a full row, ad_l first k columns, ad_b entry  
        if (pivot_row != k) {
            int cols_all = n;
            int blocks_swap_all = (cols_all + block1d - 1) / block1d;
            row_swap_kernel<<<blocks_swap_all, block1d>>>(ad_a, n, k, pivot_row, cols_all);
            check_cuda(cudaGetLastError());

            if (k > 0) {
                int cols_l = k;
                int blocks_swap_l = (cols_l + block1d - 1) / block1d;
                row_swap_kernel<<<blocks_swap_l, block1d>>>(ad_l, n, k, pivot_row, cols_l);
                check_cuda(cudaGetLastError());
            }
            vec_swap_kernel<<<1,1>>>(ad_b, k, pivot_row);
            check_cuda(cudaGetLastError());
            check_cuda(cudaDeviceSynchronize());
        }

        // Xompute L's multipliers (time for L)  
        if (k + 1 < n) {
            int elems = n - (k + 1);
            int blocks_mult = (elems + block1d - 1) / block1d;
            check_cuda(cudaEventRecord(ev_l_s));
            compute_factors_kernel<<<blocks_mult, block1d>>>(ad_a, ad_l, n, k);
            check_cuda(cudaEventRecord(ev_l_e));
            check_cuda(cudaEventSynchronize(ev_l_e));
            float ms_l = 0.0f; check_cuda(cudaEventElapsedTime(&ms_l, ev_l_s, ev_l_e));
            sum_l_ms += ms_l;
            check_cuda(cudaGetLastError());
        }

        // Udate 
        int rows = n - (k + 1);
        int cols = n - (k + 1);
        if (rows > 0 && cols > 0) {
            dim3 block(tile, tile);
            dim3 grid((cols + tile - 1) / tile, (rows + tile - 1) / tile);
            size_t sh = (size_t)tile * sizeof(double) + (size_t)tile * sizeof(double);
            check_cuda(cudaEventRecord(ev_u_s));
            subMat_kernel<<<grid, block, sh>>>(ad_a, ad_l, n, k);
            check_cuda(cudaEventRecord(ev_u_e));
            check_cuda(cudaEventSynchronize(ev_u_e));
            float ms_u = 0.0f; check_cuda(cudaEventElapsedTime(&ms_u, ev_u_s, ev_u_e));
            sum_u_ms += ms_u;
            check_cuda(cudaGetLastError());
        }
    }

    // delte evejts
    check_cuda(cudaEventDestroy(ev_l_s)); check_cuda(cudaEventDestroy(ev_l_e));
    check_cuda(cudaEventDestroy(ev_u_s)); check_cuda(cudaEventDestroy(ev_u_e));
    *gpu_L_time_ms_out = sum_l_ms;
    *gpu_U_time_ms_out = sum_u_ms;

    free(ah_blk_val); free(ah_blk_idx);
    check_cuda(cudaFree(ad_blk_val)); check_cuda(cudaFree(ad_blk_idx));
}
 
int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s input.txt output.txt\n", argv[0]);
        return EXIT_FAILURE;
    }
    const char *infile = argv[1];
    const char *outfile = argv[2];

    int ah_n = 0;
    double *ah_a = NULL;
    double *ah_b = NULL;
    double ah_read_time_ms = 0.0;

    read_input(infile, &ah_n, &ah_a, &ah_b, &ah_read_time_ms);

    int n = ah_n;
    size_t mat_bytes = (size_t)n * n * sizeof(double);
    size_t vec_bytes = (size_t)n * sizeof(double);

    // Dvice arrays  
    double *ad_a = NULL, *ad_l = NULL, *ad_b = NULL;
    check_cuda(cudaMalloc((void**)&ad_a, mat_bytes));
    check_cuda(cudaMalloc((void**)&ad_l, mat_bytes));
    check_cuda(cudaMalloc((void**)&ad_b, vec_bytes));

    // Copy inputs  
    check_cuda(cudaMemcpy(ad_a, ah_a, mat_bytes, cudaMemcpyHostToDevice));
    check_cuda(cudaMemcpy(ad_b, ah_b, vec_bytes, cudaMemcpyHostToDevice));

    // Init ad_l to identity via host buffer  
    double *ah_l_init = (double*) malloc(mat_bytes);
    if (!ah_l_init) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }
    for (int i = 0; i < n * n; ++i) ah_l_init[i] = 0.0;
    for (int i = 0; i < n; ++i) ah_l_init[i * n + i] = 1.0;
    check_cuda(cudaMemcpy(ad_l, ah_l_init, mat_bytes, cudaMemcpyHostToDevice));
    free(ah_l_init);

    // Total factorization + solve time (host)  
    struct timespec tsolve_s, tsolve_e;
    clock_gettime(CLOCK_MONOTONIC, &tsolve_s);

    // GPU factorize with measured L and U times  
    float gpu_L_ms = 0.0f, gpu_U_ms = 0.0f;
    gpu_lup_factorize(n, ad_a, ad_l, ad_b, &gpu_L_ms, &gpu_U_ms);

    // Cp back and build host L, U, permuted b  
    double *ah_l = (double*) malloc(mat_bytes);
    double *ah_u = (double*) malloc(mat_bytes);
    double *ah_b_perm = (double*) malloc(vec_bytes);
    if (!ah_l || !ah_u || !ah_b_perm) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }

    check_cuda(cudaMemcpy(ah_l, ad_l, mat_bytes, cudaMemcpyDeviceToHost));
    double *ah_a_work = (double*) malloc(mat_bytes);
    if (!ah_a_work) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }
    check_cuda(cudaMemcpy(ah_a_work, ad_a, mat_bytes, cudaMemcpyDeviceToHost));
    check_cuda(cudaMemcpy(ah_b_perm, ad_b, vec_bytes, cudaMemcpyDeviceToHost));

    // Extract U also L diag elements = 1
    for (int i = 0; i < n * n; ++i) ah_u[i] = 0.0;
    for (int i = 0; i < n; ++i) {
        ah_l[i * n + i] = 1.0;
        for (int j = i; j < n; ++j) ah_u[i * n + j] = ah_a_work[i * n + j];
    }

    // Solve on host
    double *ah_x = (double*) calloc(n, sizeof(double)); // safety  
    if (!ah_x) { fprintf(stderr,"malloc failed\n"); exit(EXIT_FAILURE); }
    host_solve(n, ah_l, ah_u, ah_b_perm, ah_x);

    clock_gettime(CLOCK_MONOTONIC, &tsolve_e);
    double total_solve_ms = (tsolve_e.tv_sec - tsolve_s.tv_sec) * 1000.0 + (tsolve_e.tv_nsec - tsolve_s.tv_nsec) / 1e6;

    // Output write
    write_output(outfile, n, ah_l, ah_u, ah_x);

    // Compute perf metrics 
    // Timing file changes 
    performance_metrics pm;
    cal_metrics(n, &pm);

    char timing_name[256];
    snprintf(timing_name, sizeof(timing_name), "timing_%d.txt", n);
    FILE *tf = fopen(timing_name, "w");
    if (tf) {
        fprintf(tf, "Timing Information for N = %d\n", n);
        fprintf(tf, "-----------------------------------------\n");
        fprintf(tf, "Time taken to read input matrices: %.6f ms\n", ah_read_time_ms);
        fprintf(tf, "Time taken to compute L : %.6f ms\n", (double)gpu_L_ms);
        fprintf(tf, "Time taken to compute U : %.6f ms\n", (double)gpu_U_ms);
        fprintf(tf, "Total time for solving linear equations: %.6f ms\n", total_solve_ms);
        fprintf(tf, "\n");
        fprintf(tf, "Performance Metrics\n");
        fprintf(tf, "-----------------------------------------\n");
        fprintf(tf, "Total FLOPs: %lld\n", pm.total_flops);
        fprintf(tf, "Total Memory Accesses(Global and Shared): %lld\n", pm.total_mem_acc);
        fprintf(tf, "CGMA : %.6f\n", pm.cgma);
        fprintf(tf, "Thread Calls: %lld\n", pm.total_thread_calls);
        fprintf(tf, "Blocks per Grid: %d\n", pm.blocks_per_grid);
        fprintf(tf, "Threads per Block: %d\n", pm.threads_per_block);
        fclose(tf);
    } else {
        fprintf(stderr, "Failed to open the timing file\n");
    }

    // Xlen
    free(ah_a); free(ah_b); free(ah_l); free(ah_u); free(ah_a_work); free(ah_b_perm); free(ah_x);
    check_cuda(cudaFree(ad_a)); check_cuda(cudaFree(ad_l)); check_cuda(cudaFree(ad_b));

    printf("Solved. Output is at -> %s  Timing and Performance metrics are at -> %s\n", outfile, timing_name);
    return 0;
}
