#include <vector>
#include <algorithm>
#include <functional>
#include <chrono>
#include <cmath>
#include <numeric>
#include <set>

class ZeroOneSolver {
private:
    std::vector<std::vector<int>> A;
    std::vector<int> b;
    std::vector<std::pair<int, int>> vars_to_try; // (index, trying_value)
    std::vector<int> current_x;
    std::vector<int> current_x_assignments;
    std::vector<std::vector<int>> successful_solutions;
    int revert_count = 0;
    std::vector<double> dof_list;
    std::vector<double> new_dof_list;
    std::vector<int> variable_order;
    bool timeout_flag = false;

    // 辅助函数：组合数计算
    double comb(int n, int k) {
        if (k < 0 || k > n) return 0;
        if (k > n - k) k = n - k;
        double result = 1;
        for (int i = 1; i <= k; ++i) {
            result = result * (n - k + i) / i;
        }
        return result;
    }

    void set_constraint_dof() {
        int rows = A.size();
        int cols = current_x.size();
        
        dof_list.resize(rows);
        new_dof_list.resize(rows);
        
        for (int constraint_index = 0; constraint_index < rows; ++constraint_index) {
            std::vector<int> unassigned_vars;
            int signed_vars = 0;
            
            for (int var_index = 0; var_index < cols; ++var_index) {
                if (A[constraint_index][var_index] == 1) {
                    if (current_x[var_index] == -1) {
                        unassigned_vars.push_back(var_index);
                    } else if (current_x[var_index] == 1) {
                        signed_vars++;
                    }
                }
            }
            
            int sum_to_assign = b[constraint_index] - signed_vars;
            dof_list[constraint_index] = comb(unassigned_vars.size(), sum_to_assign);
            
            double c1 = (unassigned_vars.size() > 0) ? comb(unassigned_vars.size() - 1, sum_to_assign) : 0;
            double c2 = (unassigned_vars.size() > 0 && sum_to_assign > 0) ? comb(unassigned_vars.size() - 1, sum_to_assign - 1) : 0;
            new_dof_list[constraint_index] = std::max(c1, c2);
        }
        
        // 计算变量顺序
        variable_order.resize(cols);
        std::iota(variable_order.begin(), variable_order.end(), 0);
        
        std::sort(variable_order.begin(), variable_order.end(), 
            [this, cols](int i, int j) {
                double ratio_i = 1.0, ratio_j = 1.0;
                int count_i = 0, count_j = 0;
                
                for (int row = 0; row < A.size(); ++row) {
                    if (A[row][i] == 1 && dof_list[row] > 0) {
                        ratio_i *= new_dof_list[row] / dof_list[row];
                        count_i++;
                    }
                    if (A[row][j] == 1 && dof_list[row] > 0) {
                        ratio_j *= new_dof_list[row] / dof_list[row];
                        count_j++;
                    }
                }
                
                if (std::abs(ratio_i - ratio_j) > 1e-9) {
                    return ratio_i < ratio_j;
                }
                return count_i > count_j;
            });
    }

    bool try_new_var() {
        std::set<int> trying_set;
        for (const auto& item : vars_to_try) {
            trying_set.insert(item.first);
        }
        
        for (int var_index : variable_order) {
            if (trying_set.find(var_index) == trying_set.end() && current_x[var_index] == -1) {
                vars_to_try.push_back({var_index, 0});
                vars_to_try.push_back({var_index, 1});
                return true;
            }
        }
        return false;
    }

    bool apply_trying_vars() {
        if (vars_to_try.empty()) return false;
        
        auto [var_index, trying_value] = vars_to_try.back();
        vars_to_try.pop_back();
        current_x[var_index] = trying_value;
        current_x_assignments.push_back(var_index);
        
        bool changed = true;
        while (changed) {
            set_constraint_dof();
            changed = false;
            
            for (int constraint_index = 0; constraint_index < A.size(); ++constraint_index) {
                if (dof_list[constraint_index] >= 1) continue;
                
                int sum_assigned = 0;
                std::vector<int> unassigned_indices;
                
                for (int var_index_2 = 0; var_index_2 < current_x.size(); ++var_index_2) {
                    if (A[constraint_index][var_index_2] == 1) {
                        if (current_x[var_index_2] == 1) {
                            sum_assigned++;
                        } else if (current_x[var_index_2] == -1) {
                            unassigned_indices.push_back(var_index_2);
                        }
                    }
                }
                
                if (sum_assigned > b[constraint_index]) {
                    return false;
                }
                
                if (sum_assigned + unassigned_indices.size() < b[constraint_index]) {
                    return false;
                }
                
                if (unassigned_indices.empty() && sum_assigned != b[constraint_index]) {
                    return false;
                }
                
                int sum_to_assign = b[constraint_index] - sum_assigned;
                if (sum_assigned == 0) {
                    for (int var_idx : unassigned_indices) {
                        current_x[var_idx] = 0;
                        current_x_assignments.push_back(var_idx);
                    }
                    changed = true;
                } else if (sum_to_assign == unassigned_indices.size()) {
                    for (int var_idx : unassigned_indices) {
                        current_x[var_idx] = 1;
                        current_x_assignments.push_back(var_idx);
                    }
                    changed = true;
                }
            }
        }
        return true;
    }

    void revert_trying_vars() {
        revert_count++;
        while (!current_x_assignments.empty()) {
            int var_index = current_x_assignments.back();
            current_x_assignments.pop_back();
            current_x[var_index] = -1;
            
            if (!vars_to_try.empty() && var_index == vars_to_try.back().first) {
                return;
            }
        }
    }

public:
    ZeroOneSolver(const std::vector<std::vector<int>>& A_input, 
                  const std::vector<int>& b_input) 
        : A(A_input), b(b_input) {
        int rows = A.size();
        int cols = (rows > 0) ? A[0].size() : 0;
        current_x.resize(cols, -1);
        set_constraint_dof();
        timeout_flag = false;
    }

    std::vector<std::vector<int>> get_solutions(int timeout_seconds = -1) {
        auto start_time = std::chrono::steady_clock::now();
        timeout_flag = false;
        successful_solutions.clear();
        revert_count = 0;
        vars_to_try.clear();
        current_x.assign(current_x.size(), -1);
        current_x_assignments.clear();
        
        try_new_var();
        
        while (true) {
            if (timeout_seconds > 0) {
                auto current_time = std::chrono::steady_clock::now();
                auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time).count();
                if (elapsed > timeout_seconds) {
                    timeout_flag = true;
                    return successful_solutions;
                }
            }
            
            if (vars_to_try.empty()) break;
            
            if (!apply_trying_vars()) {
                revert_trying_vars();
                continue;
            }
            
            bool all_assigned = true;
            for (int val : current_x) {
                if (val == -1) {
                    all_assigned = false;
                    break;
                }
            }
            
            if (all_assigned) {
                successful_solutions.push_back(current_x);
                revert_trying_vars();
                continue;
            } else {
                try_new_var();
            }
        }
        
        return successful_solutions;
    }
    
    bool get_timeout_flag() const { return timeout_flag; }
    int get_revert_count() const { return revert_count; }
    const std::vector<std::vector<int>>& get_successful_solutions() const { return successful_solutions; }
};

// 创建 C 接口包装
extern "C" {
    ZeroOneSolver* create_solver(int* A_data, int* shape, int* b_data, int b_len) {
        // 转换数据格式
        std::vector<std::vector<int>> A(shape[0], std::vector<int>(shape[1]));
        for (int i = 0; i < shape[0]; i++) {
            for (int j = 0; j < shape[1]; j++) {
                A[i][j] = A_data[i * shape[1] + j];
            }
        }
        std::vector<int> b(b_data, b_data + b_len);
        return new ZeroOneSolver(A, b);
    }
    
    void delete_solver(ZeroOneSolver* solver) {
        delete solver;
    }
    
    int** get_solutions(ZeroOneSolver* solver, int* num_solutions, int* num_vars) {
        auto solutions = solver->get_solutions();
        *num_solutions = solutions.size();
        if (solutions.empty()) return nullptr;
        
        *num_vars = solutions[0].size();
        int** result = new int*[*num_solutions];
        for (int i = 0; i < *num_solutions; i++) {
            result[i] = new int[*num_vars];
            std::copy(solutions[i].begin(), solutions[i].end(), result[i]);
        }
        return result;
    }
    
    void free_solutions(int** solutions, int num_solutions) {
        for (int i = 0; i < num_solutions; i++) {
            delete[] solutions[i];
        }
        delete[] solutions;
    }
}