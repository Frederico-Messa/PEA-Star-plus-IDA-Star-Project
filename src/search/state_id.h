#ifndef STATE_ID_H
#define STATE_ID_H

#include <iostream>

// For documentation on classes relevant to storing and working with registered
// states see the file state_registry.h.

class StateID {
    friend class StateRegistry;
    friend std::ostream &operator<<(std::ostream &os, StateID id);
    template<typename>
    friend class PerStateInformation;
    template<typename>
    friend class PerStateArray;
    friend class PerStateBitset;

    explicit StateID(int value_)
        : value(value_) {
    }

    // No implementation to prevent default construction
    StateID();
public:
    ~StateID() {
    }

    static const StateID no_state;

    bool operator==(const StateID &other) const {
        return value == other.value;
    }

    bool operator!=(const StateID &other) const {
        return !(*this == other);
    }

    int value;

    StateID(int value_, bool are_you_sure_you_want_to_contruct_a_state_id) : value(value_)
    {
        if(not are_you_sure_you_want_to_contruct_a_state_id)
        {
            throw new std::exception();
        }
    };
};

template <>
struct std::hash<StateID>
{
    std::size_t operator()(StateID const &state_id) const noexcept
    {
        return state_id.value;
    }
};

#endif
