#ifndef SEARCH_STATISTICS_H
#define SEARCH_STATISTICS_H

/*
  This class keeps track of search statistics.

  It keeps counters for expanded, generated and evaluated states (and
  some other statistics) and provides uniform output for all search
  methods.
*/

namespace utils {
enum class Verbosity;
}

class SearchStatistics {
    const utils::Verbosity verbosity;

    // General statistics
    long long int expanded_states;  // no states for which successors were generated
    long long int evaluated_states; // no states for which h fn was computed
    long long int evaluations;      // no of heuristic evaluations performed
    long long int generated_states; // no states created in total (plus those removed since already in close list)
    long long int reopened_states;  // no of *closed* states which we reopened
    long long int dead_end_states;

    long long int generated_ops;    // no of operators that were returned as applicable

    // Statistics related to f values
    int lastjump_f_value; //f value obtained in the last jump
    long long int lastjump_expanded_states; // same guy but at point where the last jump in the open list
    long long int lastjump_reopened_states; // occurred (jump == f-value of the first node in the queue increases)
    long long int lastjump_evaluated_states;
    long long int lastjump_generated_states;

    void print_f_line() const;
public:
    explicit SearchStatistics(utils::Verbosity verbosity);
    ~SearchStatistics() = default;

    // Methods that update statistics.
    void inc_expanded(long long int inc = 1) {expanded_states += inc;}
    void inc_evaluated_states(long long int inc = 1) {evaluated_states += inc;}
    void inc_generated(long long int inc = 1) {generated_states += inc;}
    void inc_reopened(long long int inc = 1) {reopened_states += inc;}
    void inc_generated_ops(long long int inc = 1) {generated_ops += inc;}
    void inc_evaluations(long long int inc = 1) {evaluations += inc;}
    void inc_dead_ends(long long int inc = 1) {dead_end_states += inc;}

    // Methods that access statistics.
    long long int get_expanded() const {return expanded_states;}
    long long int get_evaluated_states() const {return evaluated_states;}
    long long int get_evaluations() const {return evaluations;}
    long long int get_generated() const {return generated_states;}
    long long int get_reopened() const {return reopened_states;}
    long long int get_generated_ops() const {return generated_ops;}

    /*
      Call the following method with the f value of every expanded
      state. It will notice "jumps" (i.e., when the expanded f value
      is the highest f value encountered so far), print some
      statistics on jumps, and keep track of expansions etc. up to the
      last jump.

      Statistics until the final jump are often useful to report in
      A*-style searches because they are not affected by tie-breaking
      as the overall statistics. (With a non-random, admissible and
      consistent heuristic, the number of expanded, evaluated and
      generated states until the final jump is fully determined by the
      state space and heuristic, independently of things like the
      order in which successors are generated or the tie-breaking
      performed by the open list.)
    */
    void report_f_value_progress(int f);
    void print_checkpoint_line(int g) const;

    // output
    void print_basic_statistics() const;
    void print_detailed_statistics() const;
};

#endif
