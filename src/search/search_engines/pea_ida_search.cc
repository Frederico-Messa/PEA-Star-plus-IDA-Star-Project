#include "pea_ida_search.h"

#include "../evaluation_context.h"
#include "../evaluator.h"
#include "../option_parser.h"

#include "../algorithms/ordered_set.h"
#include "../task_utils/task_properties.h"
#include "../task_utils/successor_generator.h"

#include "../utils/logging.h"

#include <cassert>
#include <cstdlib>
#include <memory>
#include <optional.hh>
#include <set>

#include <climits>

using namespace std;

namespace pea_ida_search
{
    PeaIdaSearch::PeaIdaSearch(const Options &opts)
        : SearchEngine(opts),
          h_evaluator(opts.get<shared_ptr<Evaluator>>("eval"))
    {
    }

    void PeaIdaSearch::initialize()
    {
        State initial_state = state_registry.get_initial_state();

        EvaluationContext eval_context(initial_state, 0, false, &statistics);
        int initial_h_value = eval_context.get_evaluator_value_or_infinity(h_evaluator.get());
        statistics.inc_evaluated_states();

        first_phase_initial_node = {initial_state.get_id(), 0, initial_h_value, 0};

        if (initial_h_value != INT_MAX)
        {
            push_in_first_phase_open_queue(first_phase_initial_node);
        }

        current_phase = FIRST_PHASE;
        second_phase_needed = false;
        open_peak_size = 0;
        closed_peak_size = 0;
        number_of_first_phase_expansions = 0;
        number_of_second_phase_expansions = 0;
        number_of_first_phase_generations = 0;
        number_of_second_phase_generations = 0;
        number_of_second_phase_transitions = 0;
        expanding = false;
    }

    void PeaIdaSearch::print_statistics() const
    {
        statistics.print_detailed_statistics();
        search_space.print_statistics();
    }

    SearchStatus PeaIdaSearch::step()
    {
        open_peak_size = max(open_peak_size, first_phase_open_queue.size());
        closed_peak_size = max(closed_peak_size, first_phase_closed_hash.size());

        if (current_phase == FIRST_PHASE)
        {
            return first_phase_step();
        }
        if (current_phase == SECOND_PHASE)
        {
            return second_phase_step();
        }
    }

    SearchStatus PeaIdaSearch::first_phase_step()
    {
        if (expanding)
        {
            if (not expanding_operators.empty())
            {
                OperatorID applicable_operator = expanding_operators.back();
                expanding_operators.pop_back();

                State expanding_state = state_registry.lookup_state(expanding_node.state_id);
                OperatorProxy applicable_operator_proxy = task_proxy.get_operators()[applicable_operator];
                State successor_state = state_registry.get_successor_state(expanding_state, applicable_operator_proxy);
                statistics.inc_generated();
                number_of_first_phase_generations++;

                StateID successor_state_id = successor_state.get_id();
                int successor_g_value = expanding_node.g_value + applicable_operator_proxy.get_cost();

                if (expanding_hash.find(successor_state_id) != expanding_hash.end() and expanding_hash[successor_state_id] <= successor_g_value)
                {
                    return IN_PROGRESS;
                }

                if (first_phase_closed_hash.find(successor_state_id) != first_phase_closed_hash.end())
                {
                    if (first_phase_closed_hash[successor_state_id] <= successor_g_value)
                    {
                        return IN_PROGRESS;
                    }

                    first_phase_closed_hash.erase(successor_state_id);
                }

                if (first_phase_open_queue_hash.find(successor_state_id) != first_phase_open_queue_hash.end())
                {
                    if (first_phase_open_queue_hash[successor_state_id].first <= successor_g_value)
                    {
                        return IN_PROGRESS;
                    }

                    pop_from_first_phase_open_queue(first_phase_open_queue_hash[successor_state_id].second);
                }

                EvaluationContext eval_context(successor_state, successor_g_value, false, &statistics);
                int successor_h_value = eval_context.get_evaluator_value_or_infinity(h_evaluator.get());
                statistics.inc_evaluated_states();

                if (successor_h_value == INT_MAX)
                {
                    return IN_PROGRESS;
                }

                generating_nodes.push_back({successor_state_id, successor_g_value, successor_g_value + successor_h_value, expanding_node.depth + 1});

                first_phase_generating_operators_proxy_ids[successor_state_id] = applicable_operator_proxy.get_id();
                first_phase_predecessors_state_ids_values[successor_state_id] = expanding_node.state_id.value;
                expanding_hash[successor_state_id] = successor_g_value;

                return IN_PROGRESS;
            }

            int new_big_f_value = INT_MAX;
            vector<OpenNode> generating_nodes_to_put_in_open;
            vector<OpenNode> generating_nodes_to_re_compact;

            while (not generating_nodes.empty())
            {
                OpenNode generating_node = generating_nodes.back();
                generating_nodes.pop_back();

                if (expanding_hash[generating_node.state_id] < generating_node.g_value)
                {
                    continue;
                }

                if (using_partial_expansion and generating_node.big_f_value > expanding_node.big_f_value)
                {
                    generating_nodes_to_re_compact.push_back(generating_node);
                    new_big_f_value = min(new_big_f_value, generating_node.big_f_value);
                }
                else
                {
                    generating_nodes_to_put_in_open.push_back(generating_node);
                }
            }

            if (first_phase_open_queue.size() + generating_nodes_to_put_in_open.size() + min((long unsigned int)1, generating_nodes_to_re_compact.size()) > open_limit)
            {
                print_infos_about_big_f_values_at_phase_transition();
                print_infos_about_depths_at_phase_transition();
                second_phase_needed = true;

                push_in_first_phase_open_queue(expanding_node);
            }
            else
            {
                if (generating_nodes_to_re_compact.size() == 0)
                {
                    first_phase_closed_hash[expanding_node.state_id] = expanding_node.g_value;
                }
                else if (generating_nodes_to_re_compact.size() == 1)
                {
                    first_phase_closed_hash[expanding_node.state_id] = expanding_node.g_value;
                    generating_nodes_to_put_in_open.push_back(generating_nodes_to_re_compact.back());
                }
                else
                {
                    expanding_node.big_f_value = new_big_f_value;

                    push_in_first_phase_open_queue(expanding_node);
                }

                while (not generating_nodes_to_put_in_open.empty())
                {
                    OpenNode generating_node = generating_nodes_to_put_in_open.back();
                    generating_nodes_to_put_in_open.pop_back();

                    push_in_first_phase_open_queue(generating_node);
                }
            }

            expanding = false;
        }
        else
        {
            if (first_phase_open_queue.empty())
            {
                print_solution(true);
                return FAILED;
            }

            expanding_node = pop_from_first_phase_open_queue();

            if (second_phase_needed)
            {
                if (second_phase_lower_bound.has_value() and second_phase_lower_bound.value() > expanding_node.big_f_value) // A*+IDA* \uparrow
                {
                    expanding_node.big_f_value = second_phase_lower_bound.value();
                    push_in_first_phase_open_queue(expanding_node);
                }
                else
                {
                    second_phase_initial_node = expanding_node;
                    second_phase_initial_node_new_big_f_value = INT_MAX;
                    second_phase_open_queue.push(second_phase_initial_node);

                    current_phase = SECOND_PHASE;
                    number_of_second_phase_transitions++;
                }
                return IN_PROGRESS;
            }

            State expanding_state = state_registry.lookup_state(expanding_node.state_id);

            if (task_properties::is_goal_state(task_proxy, expanding_state))
            {
                print_solution();
                return SOLVED;
            }

            statistics.inc_expanded();
            number_of_first_phase_expansions++;
            successor_generator.generate_applicable_ops(expanding_state, expanding_operators);
            expanding_hash = {}; // Avoids generating two nodes with same state, or a node with the same state as the expanding node.
            expanding_hash[expanding_node.state_id] = expanding_node.g_value;

            expanding = true;
        }
        return IN_PROGRESS;
    }

    SearchStatus PeaIdaSearch::second_phase_step()
    {
        if (expanding)
        {
            if (not expanding_operators.empty())
            {
                OperatorID applicable_operator = expanding_operators.back();
                expanding_operators.pop_back();

                State expanding_state = state_registry.lookup_state(expanding_node.state_id);
                OperatorProxy applicable_operator_proxy = task_proxy.get_operators()[applicable_operator];
                State successor_state = state_registry.get_successor_state(expanding_state, applicable_operator_proxy);
                statistics.inc_generated();
                number_of_second_phase_generations++;

                StateID successor_state_id = successor_state.get_id();

                for (int ancestral_state_id_value: second_phase_predecessors_state_ids_values)
                {
                    if (successor_state_id.value == ancestral_state_id_value)
                    {
                        return IN_PROGRESS;
                    }
                }
                int ancestral_state_id_value = second_phase_initial_node.state_id.value;
                while (ancestral_state_id_value != first_phase_initial_node.state_id.value)
                {
                    ancestral_state_id_value = first_phase_predecessors_state_ids_values[StateID(ancestral_state_id_value, true)];
                    if (successor_state_id.value == ancestral_state_id_value)
                    {
                        return IN_PROGRESS;
                    }
                }

                int successor_g_value = expanding_node.g_value + applicable_operator_proxy.get_cost();

                if (expanding_hash.find(successor_state_id) != expanding_hash.end() and expanding_hash[successor_state_id] <= successor_g_value)
                {
                    return IN_PROGRESS;
                }

                EvaluationContext eval_context(successor_state, successor_g_value, false, &statistics);
                int successor_h_value = eval_context.get_evaluator_value_or_infinity(h_evaluator.get());
                statistics.inc_evaluated_states();

                if (successor_h_value == INT_MAX)
                {
                    return IN_PROGRESS;
                }

                if (successor_g_value + successor_h_value > second_phase_initial_node.big_f_value)
                {
                    second_phase_initial_node_new_big_f_value = min(second_phase_initial_node_new_big_f_value, successor_g_value + successor_h_value);
                    return IN_PROGRESS;
                }

                generating_nodes.push_back({successor_state_id, successor_g_value, successor_g_value + successor_h_value, expanding_node.depth + 1});

                second_phase_generating_operators_proxy_ids.back()[successor_state_id] = applicable_operator_proxy.get_id();
                expanding_hash[successor_state_id] = successor_g_value;

                return IN_PROGRESS;
            }

            while (not generating_nodes.empty())
            {
                OpenNode generating_node = generating_nodes.back();
                generating_nodes.pop_back();

                if (expanding_hash[generating_node.state_id] < generating_node.g_value)
                {
                    continue;
                }

                second_phase_open_queue.push(generating_node);
            }

            expanding = false;
        }
        else
        {
            if (second_phase_open_queue.empty())
            {
                if (second_phase_initial_node_new_big_f_value != INT_MAX)
                {
                    second_phase_initial_node.big_f_value = second_phase_initial_node_new_big_f_value;
                    push_in_first_phase_open_queue(second_phase_initial_node);
                }
                else
                {
                    first_phase_closed_hash[second_phase_initial_node.state_id] = second_phase_initial_node.g_value;
                }

                current_phase = FIRST_PHASE;
                return IN_PROGRESS;
            }

            expanding_node = second_phase_open_queue.top();
            second_phase_open_queue.pop();

            while (second_phase_predecessors_state_ids_values.size() > expanding_node.depth - second_phase_initial_node.depth)
            {
                second_phase_predecessors_state_ids_values.pop_back();
                second_phase_generating_operators_proxy_ids.pop_back();
            }

            State expanding_state = state_registry.lookup_state(expanding_node.state_id);

            if (task_properties::is_goal_state(task_proxy, expanding_state))
            {
                print_solution();
                return SOLVED;
            }

            statistics.inc_expanded();
            number_of_second_phase_expansions++;
            successor_generator.generate_applicable_ops(expanding_state, expanding_operators);
            expanding_hash = {}; // Avoids generating two nodes with same state, or a node with the same state as the expanding node.
            expanding_hash[expanding_node.state_id] = expanding_node.g_value;

            second_phase_predecessors_state_ids_values.push_back(expanding_node.state_id.value);
            second_phase_generating_operators_proxy_ids.push_back(Hash());

            expanding = true;
        }
        return IN_PROGRESS;
    }

    PeaIdaSearch::OpenNode PeaIdaSearch::pop_from_first_phase_open_queue(optional<PeaIdaSearch::FBestQueue::handle_type> handle)
    {
        OpenNode open_node;
        if (handle.has_value())
        {
            open_node = **handle;
            first_phase_open_queue.erase(*handle);
        }
        else
        {
            open_node = first_phase_open_queue.top();
            first_phase_open_queue.pop();
        }

        first_phase_open_queue_hash.erase(open_node.state_id);

        return open_node;
    }

    void PeaIdaSearch::push_in_first_phase_open_queue(PeaIdaSearch::OpenNode open_node)
    {
        FBestQueue::handle_type handle = first_phase_open_queue.push(open_node);
        first_phase_open_queue_hash[open_node.state_id] = std::pair<int, FBestQueue::handle_type>{open_node.g_value, handle};
    }

    void PeaIdaSearch::print_solution(bool insolution)
    {
        if (insolution)
        {
            utils::g_log << "Insolution found!" << endl;
        }
        else
        {
            utils::g_log << "Solution found!" << endl;

            Plan plan;
            int ancestral_state_id_value = expanding_node.state_id.value;
            while (not second_phase_predecessors_state_ids_values.empty())
            {
                plan.push_back(OperatorID(second_phase_generating_operators_proxy_ids.back()[StateID(ancestral_state_id_value, true)]));
                ancestral_state_id_value = second_phase_predecessors_state_ids_values.back();
                second_phase_generating_operators_proxy_ids.pop_back();
                second_phase_predecessors_state_ids_values.pop_back();
            }
            while (ancestral_state_id_value != first_phase_initial_node.state_id.value)
            {
                plan.push_back(OperatorID(first_phase_generating_operators_proxy_ids[StateID(ancestral_state_id_value, true)]));
                ancestral_state_id_value = first_phase_predecessors_state_ids_values[StateID(ancestral_state_id_value, true)];
            }
            reverse(plan.begin(), plan.end());
            set_plan(plan);
        }

        utils::g_log << "Open peak size: " << open_peak_size << endl;
        utils::g_log << "Closed peak size: " << closed_peak_size << endl;
        utils::g_log << "Number of first phase expansions: " << number_of_first_phase_expansions << endl;
        utils::g_log << "Number of second phase expansions: " << number_of_second_phase_expansions << endl;
        utils::g_log << "Number of first phase generations: " << number_of_first_phase_generations << endl;
        utils::g_log << "Number of second phase generations: " << number_of_second_phase_generations << endl;
        utils::g_log << "Number of second phase iterations: " << number_of_second_phase_transitions << endl;
    }

    void PeaIdaSearch::print_infos_about_big_f_values_at_phase_transition()
    {
        int min_big_f_value = expanding_node.big_f_value;
        int max_big_f_value = expanding_node.big_f_value;
        long long int sum_of_big_f_value = expanding_node.big_f_value;
        unsigned long int count_of_min_big_f_value = 1;

        FBestQueue::iterator first_phase_open_queue_iterator = first_phase_open_queue.begin();
        for (unsigned long int i = 0; i < first_phase_open_queue.size(); i++)
        {
            int big_f_value = first_phase_open_queue_iterator->big_f_value;
            sum_of_big_f_value += big_f_value;
            max_big_f_value = max(max_big_f_value, big_f_value);

            if (big_f_value == min_big_f_value)
            {
                count_of_min_big_f_value++;
            }

            std::advance(first_phase_open_queue_iterator, 1);
        }

        float percentage_of_min_big_f_values = {float(count_of_min_big_f_value) / float(first_phase_open_queue.size() + 1)};
        float mean_big_f_value = {float(sum_of_big_f_value) / float(first_phase_open_queue.size() + 1)};

        utils::g_log << "Mininum F-value at phase transition: " << min_big_f_value << endl;
        utils::g_log << "Mean F-value at phase transition: " << mean_big_f_value << endl;
        utils::g_log << "Maximum F-value at phase transition: " << max_big_f_value << endl;
        utils::g_log << "Percentage of minimum F-values at phase transition: " << percentage_of_min_big_f_values << endl;
    }

    void PeaIdaSearch::print_infos_about_depths_at_phase_transition()
    {
        int min_depth = expanding_node.depth;
        int max_depth = expanding_node.depth;
        long long int sum_of_depth = expanding_node.depth;

        FBestQueue::iterator first_phase_open_queue_iterator = first_phase_open_queue.begin();
        for (unsigned long int i = 0; i < first_phase_open_queue.size(); i++)
        {
            int depth = first_phase_open_queue_iterator->depth;
            sum_of_depth += depth;
            max_depth = max(max_depth, depth);
            min_depth = min(min_depth, depth);

            std::advance(first_phase_open_queue_iterator, 1);
        }

        float mean_depth = {float(sum_of_depth) / float(first_phase_open_queue.size() + 1)};

        utils::g_log << "Mininum depth at phase transition: " << min_depth << endl;
        utils::g_log << "Mean depth at phase transition: " << mean_depth << endl;
        utils::g_log << "Maximum depth at phase transition: " << max_depth << endl;
    }

    void add_options_to_parser(OptionParser &parser)
    {
        SearchEngine::add_pruning_option(parser);
        SearchEngine::add_options_to_parser(parser);
    }
}
