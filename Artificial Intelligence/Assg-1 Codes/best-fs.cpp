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
    vector<vector<int>> formula_int;
    set<int> variables;

public:
    vector<vector<int>> parseStr(string& str){
        vector<string> clauses_str;
        char ch = '^';
        StringProcessing processor;
        processor.advTokenizer(str, ch, clauses_str);

        vector<vector<int>> parsed_formula_int;
        for(string& clause_str: clauses_str){
            string inner_clause = clause_str;
            inner_clause.erase(inner_clause.begin());
            inner_clause.pop_back();
            processor.removeSpace(inner_clause);

            stringstream ss(inner_clause);
            string literal_str;
            vector<int> clause_literals_int;
            while(getline(ss, literal_str, 'v')){
                clause_literals_int.push_back(stoi(literal_str));
            }
            parsed_formula_int.push_back(clause_literals_int);
        }
        return parsed_formula_int;
    }

    set<int> setVars(const vector<vector<int>>& f){
        set<int> vars_set;
        for(const auto& clause: f){
            for(int literal: clause){
                vars_set.insert(abs(literal));
            }
        }
        return vars_set;
    }

    ThreeSAT(string& str){
        formula_int = parseStr(str);
        variables = setVars(formula_int);
    }

    vector<vector<int>>& getFormula() {
        return formula_int;
    }

    set<int>& getVars() {
        return variables;
    }

    bool isSatisfied(const map<int, bool>& assignment) {
        if (assignment.size() != variables.size()) {
            return false;
        }

        for(const auto& clause: formula_int){
            bool clauseSatisfied = false;
            for(int literal: clause){
                int var = abs(literal);
                bool var_val = assignment.at(var);

                if ((literal > 0 && var_val == true) || (literal < 0 && var_val == false)){
                    clauseSatisfied = true;
                    break;
                }
            }
            if(!clauseSatisfied)
                return false;
        }
        return true;
    }

    int heuristicCost(map<int, bool>& assign, vector<vector<int>>& clauses) {
        int totalcost = 0;
 
        for (const auto& c : clauses) {
            bool clauseOk = false;
            bool unassignedVar = false;

            for (int lit : c) {
                int varId = abs(lit);
                bool negFlag = (lit < 0);

                auto it = assign.find(varId);
                if (it != assign.end()) {
                    bool val = it->second;

                    if ((val && !negFlag) || (!val && negFlag)) {
                        clauseOk = true;
                        break;
                    }
                } else {
                    unassignedVar = true;
                }
            }

            if (clauseOk) continue;

            if (!unassignedVar) {
                return INT_MAX/2;
            }
            totalcost += 1;
        }
        return totalcost;
    }

    int findUnassignedVar(const map<int, bool>& assignment) {
        for(int var: variables){
            if(assignment.find(var) == assignment.end()){
                return var;
            }
        }
        return -1;
    }
};
struct state {
    map<int, bool> assignment;
    int heuristic_cost;

    bool operator>(const state& other) const {
        return heuristic_cost > other.heuristic_cost;
    }
};

map<int, bool> bestFirstSearch(ThreeSAT& prob){
    priority_queue<state, vector<state>, greater<state>> pq;

    state initialState;
    initialState.assignment = {};
    initialState.heuristic_cost = prob.heuristicCost(initialState.assignment, prob.getFormula());
    pq.push(initialState);

    set<vector<pair<int, bool>>> visited;

    while(!pq.empty()){
        state currentState = pq.top();
        pq.pop();

        vector<pair<int, bool>> assignment_vec(currentState.assignment.begin(), currentState.assignment.end());
        sort(assignment_vec.begin(), assignment_vec.end());
        if(visited.count(assignment_vec)){
            continue;
        }
        visited.insert(assignment_vec);

        if(currentState.assignment.size() == prob.getVars().size()){
            if(prob.isSatisfied(currentState.assignment)){
                return currentState.assignment;
            }
        }

        int unassignedVar = prob.findUnassignedVar(currentState.assignment);
        if(unassignedVar != -1){
            state stateTrue;
            stateTrue.assignment = currentState.assignment;
            stateTrue.assignment[unassignedVar] = true;
            stateTrue.heuristic_cost = prob.heuristicCost(stateTrue.assignment, prob.getFormula());
            pq.push(stateTrue);

            state stateFalse;
            stateFalse.assignment = currentState.assignment;
            stateFalse.assignment[unassignedVar] = false;
            stateFalse.heuristic_cost = prob.heuristicCost(stateFalse.assignment, prob.getFormula());
            pq.push(stateFalse);
        }
    }
    return {};
}

int main() {
   
    string str;
    getline(cin, str);

    StringProcessing processor;
    if(!processor.isValid(str)){
        cout<<"Invalid"<<endl;
        return 0;
    }
    ThreeSAT prob(str);

    map<int, bool> solution = bestFirstSearch(prob);
    if(!solution.empty()){
        cout<<"Solution found! "<<endl;
        cout<<"The Satisfying Assignment is: {";
        for(auto ele: solution){
            cout<<ele.first<<"->"<< (ele.second ? "True" : "False")<<", ";
        }
        cout<<"}"<<endl;
    }
    else{
        cout <<"No Solution found"<<endl;
    }
    return 0;
}
