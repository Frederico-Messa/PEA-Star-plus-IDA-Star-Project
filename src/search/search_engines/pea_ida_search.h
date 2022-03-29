#ifndef SEARCH_ENGINES_EAGER_SEARCH_H
#define SEARCH_ENGINES_EAGER_SEARCH_H

#include "../search_engine.h"

#include <vector>

#include <boost/heap/pairing_heap.hpp>

#include <unordered_map>
#include <optional>

class Evaluator;

namespace options
{
    class OptionParser;
    class Options;
}

enum Phase
{
    FIRST_PHASE,
    SECOND_PHASE
};

namespace pea_ida_search
{
    class PeaIdaSearch : public SearchEngine
    {
        std::shared_ptr<Evaluator> h_evaluator;

        struct OpenNode
        {
            StateID state_id;
            int g_value;
            int big_f_value;
            int depth;

            OpenNode() : state_id(-1, true)
            {
            }

            OpenNode(StateID state_id, int g_value, int big_f_value, int depth) : state_id(state_id), g_value(g_value), big_f_value(big_f_value), depth(depth)
            {
            }
        };

        struct FBestOrdering
        {
            bool operator()(const OpenNode open_node_1, const OpenNode open_node_2) const
            {
                if (open_node_1.big_f_value not_eq open_node_2.big_f_value)
                {
                    return open_node_1.big_f_value > open_node_2.big_f_value;
                }

                if (open_node_1.g_value not_eq open_node_2.g_value)
                {
                    return open_node_1.g_value < open_node_2.g_value;
                }

                if (open_node_1.depth not_eq open_node_2.depth)
                {
                    return open_node_1.depth < open_node_2.depth;
                }

                return true;
            }
        };

        struct DepthOrdering
        {
            bool operator()(const OpenNode open_node_1, const OpenNode open_node_2) const
            {
                if (open_node_1.depth not_eq open_node_2.depth)
                {
                    return open_node_1.depth < open_node_2.depth;
                }

                if (open_node_1.big_f_value not_eq open_node_2.big_f_value)
                {
                    return open_node_1.big_f_value > open_node_2.big_f_value;
                }

                if (open_node_1.g_value not_eq open_node_2.g_value)
                {
                    return open_node_1.g_value < open_node_2.g_value;
                }

                return true;
            }
        };

        typedef boost::heap::pairing_heap<OpenNode, boost::heap::stable<true>, boost::heap::compare<FBestOrdering>> FBestQueue;
        typedef boost::heap::pairing_heap<OpenNode, boost::heap::stable<true>, boost::heap::compare<DepthOrdering>> DepthQueue;

        typedef std::unordered_map<StateID, std::pair<int, FBestQueue::handle_type>> FBestQueueHash;
        typedef std::unordered_map<StateID, FBestQueue::handle_type> FBestQueueSingleHash;
        typedef std::unordered_map<StateID, int> Hash;

        Phase current_phase;
        bool second_phase_needed;
        long unsigned int open_peak_size;
        long unsigned int closed_peak_size;
        long unsigned int number_of_first_phase_expansions;
        long unsigned int number_of_second_phase_expansions;
        long unsigned int number_of_first_phase_generations;
        long unsigned int number_of_second_phase_generations;
        long unsigned int number_of_second_phase_transitions;

        bool expanding;
        OpenNode expanding_node;
        std::vector<OperatorID> expanding_operators;
        std::vector<OpenNode> generating_nodes;
        Hash expanding_hash;

        FBestQueue first_phase_open_queue;
        FBestQueueHash first_phase_open_queue_hash;
        Hash first_phase_closed_hash;
        DepthQueue second_phase_open_queue;

        Hash first_phase_predecessors_state_ids_values;
        Hash first_phase_generating_operators_proxy_ids;
        std::vector<int> second_phase_predecessors_state_ids_values;
        std::vector<Hash> second_phase_generating_operators_proxy_ids;
        OpenNode first_phase_initial_node;
        OpenNode second_phase_initial_node;
        int second_phase_initial_node_new_big_f_value;

        SearchStatus first_phase_step();
        SearchStatus second_phase_step();

        OpenNode pop_from_first_phase_open_queue(std::optional<FBestQueue::handle_type> handle = {});
        void push_in_first_phase_open_queue(OpenNode open_node);

        void print_solution(bool insolution = false);

        void print_infos_about_big_f_values_at_phase_transition();
        void print_infos_about_depths_at_phase_transition();

    protected:
        virtual void initialize() override;
        virtual SearchStatus step() override;

    public:
        explicit PeaIdaSearch(const options::Options &opts);
        virtual ~PeaIdaSearch() = default;

        virtual void print_statistics() const override;
    };

    extern void add_options_to_parser(options::OptionParser &parser);
}

#endif
