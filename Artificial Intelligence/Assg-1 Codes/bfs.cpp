#include<bits/stdc++.h>
using namespace std;

class StringProcessing {
public:
    void advTokenizer(const string& str, char ch, vector<string>& tokens){
        stringstream ss(str);
        string token;
        while(getline(ss, token, ch)){
            if(!token.empty()){
                while(!token.empty() && isspace(token.front())) 
                    token.erase(token.begin());  
                while(!token.empty() && isspace(token.back())) 
                    token.pop_back();
                if(!token.empty())
                    tokens.push_back(token);
            }    
        }
    }
    bool isValid(const string& str){
        vector<string> clauses;
        char ch = '^';
        advTokenizer(str, ch, clauses);
        for(const auto& clause: clauses){
            set<int> literals;
            int lc = 0;
            int orc = 0;
            int n = clause.length();
            // cout<<clause<<endl;
            for(int i = 0; i < n; i++){
                bool neg = false;
                if(clause[i] == 'v'){
                    orc++;
                }
                if(clause[i] == '-'){
                    neg = true;
                    i++;
                }
                if(isdigit(clause[i])){
                    int lit = 0;
                    while(i < n && isdigit(clause[i])){
                        lit = lit * 10 + (clause[i] - '0');
                        i++;
                    }
                    int key = neg ? -lit : lit;
                    if(literals.count(key)){
                        cout << "Literal "<< key << " is already present in this clause \n";
                        return false;
                    }
                    literals.insert(key);
                    lc++;
                }
                else    
                    continue;
            }
            // for(auto ele: literals){
            //     cout << ele << " ";
            // }
            if(lc != 3){
                cout << "Clause " << clause << " does not have exactly 3 literals \n";
                return false;
            }
            if(orc != 2){
                cout << "Clause " << clause << " does not have exactly 2 OR operators \n";
                return false;
            }
        }
        return true;
    }

    void removeSpace(string& str){
        string temp = "";
        for(int i = 0; i < str.length(); i++){
            if(str[i] != ' ')
                temp += str[i];
        }
        str = temp;
    }
};

class ThreeSAT {
private: 
    vector<string> formula;
    set<int> literals;
public:

    vector<string> parseStr(string& str){
        vector<string> clauses;
        char ch = '^';
        StringProcessing processor;
        processor.advTokenizer(str, ch, clauses);
        vector<string> parsed_formula;
        for(string& clause: clauses){
            // remove the parentheses
            string parsed_clause = clause;
            parsed_clause.erase(parsed_clause.begin());
            parsed_clause.pop_back();
            processor.removeSpace(parsed_clause);
            stringstream ss(parsed_clause);
            string literal;
            vector<int> literals;
            while(!ss.eof()){
                getline(ss, literal, 'v');
                literals.push_back(stoi(literal));
            }
            parsed_formula.push_back(parsed_clause);
        }
        return parsed_formula;
    }

    set<int> setVars(vector<string>& formula){
        set<int> literals;
        for(auto clause: formula){
            int n = clause.length();
            for(int i = 0; i < n; i++){
                int lit = 0;
                int sign = 1;
                if(clause[i] == '-'){
                    sign = -1;
                    i++;
                }
                if(isdigit(clause[i])){
                    while(i < n && isdigit(clause[i])){
                        lit = lit * 10 + (clause[i] - '0');
                        i++;
                    }
                    literals.insert(lit);
                }
            }
        }
        return literals;
    }

    ThreeSAT(string& str){
        formula = parseStr(str);
        literals = setVars(formula);
    }

    vector<string> getFormula() {
        return formula;
    }

    set<int> getVars() {
        return literals;
    }

    bool isSatisfied(const map<int, int>& assignment){
        for(auto clause: formula){
            bool clauseSatisfied = false;
            int n = clause.length();
            for(int i = 0; i < n; i++){
                int lit = 0, sign = 1;
                if(clause[i] == '-'){
                    sign = -1;
                    i++;
                }
                if(isdigit(clause[i])){
                    while(i < n && isdigit(clause[i])){
                        lit = lit * 10 + (clause[i] - '0');
                        i++;
                    }
                    lit *= sign;
                    if(assignment.find(abs(lit)) != assignment.end()){
                        if((assignment.at(abs(lit)) == 1 && sign == 1) || (assignment.at(abs(lit)) == 0 && sign == -1)){
                            clauseSatisfied = true;
                            break;
                        }
                    }
                }
            }
            if(!clauseSatisfied)
                return false;
        }
        return true;
    }

    int findUnassignedVar(const map<int, int>& assignment){
        for(auto var: literals){
            if(assignment.find(abs(var)) == assignment.end()){
                return abs(var);
            }
        }
        return -1; // All variables are assigned
    }

};

map<int, int> bfs(ThreeSAT& prob){
    // Implementation of BFS algorithm to solve 3-SAT problem can be added here
    queue<map<int, int>> q;
    map<int, int> initialAssignment;
    q.push(initialAssignment);
    set<vector<pair<int, int>>> visited;
    while(!q.empty()){
        auto currentAssignment = q.front();
        q.pop();

        vector<pair<int, int>> assignment_vec(currentAssignment.begin(), currentAssignment.end()); 
        sort(assignment_vec.begin(), assignment_vec.end()); 
        if(visited.count(assignment_vec)){
            continue;
        }
        visited.insert(assignment_vec);

        if(currentAssignment.size() == prob.getVars().size()){
            if(prob.isSatisfied(currentAssignment)){
                return currentAssignment;
            }
        }

        // if(assignment_vec.empty()){
        //     cout<<"I am Empty"<<endl;
        // }
        // for(auto it: assignment_vec){
        //     cout<<"First : "<< it.first<< " , Second: "<<it.second<<endl;
        // }
        int unassignedVar = prob.findUnassignedVar(currentAssignment);
        // cout<<unassignedVar<<endl;
        if(unassignedVar == -1){
            continue;
        }
        // Create new assignments by assigning true (1) and false (0) to the unassigned variable
        map<int, int> assignmentTrue = currentAssignment;
        assignmentTrue[unassignedVar] = 1;
        q.push(assignmentTrue);

        map<int, int> assignmentFalse = currentAssignment;
        assignmentFalse[unassignedVar] = 0;
        q.push(assignmentFalse);
    }
    return {};
}

int main() {
    
    int t;
    cin>>t;
    getchar();
    while(t--){
        string str;
        getline(cin, str);

        StringProcessing processor;
        if(!processor.isValid(str)){
            cout<<"Invalid"<<endl;
            break;
        }
        ThreeSAT prob(str);
        // vector<string> booleanFormula = prob.getFormula();
        // for(auto ele: booleanFormula){
        //     cout<<ele<<endl;
        // }

        // set<int> literals = prob.getVars();
        // for(auto ele: literals){
        //     cout<<ele<<' ';
        // }
        // cout<<endl;

        map<int, int> solution = bfs(prob);
        if(!solution.empty()){
            cout<<"Solution found! "<<endl;
            cout<<"The Satisfying Assignment is: { ";
            for(auto ele: solution){
                cout<<ele.first<<" -> "<< (ele.second == 1 ? "True" : "False")<<", ";
            }
            cout<<"}"<<endl;
        }
        else{
            cout <<" No Solution found"<<endl;
        }
    }
    return 0;
}