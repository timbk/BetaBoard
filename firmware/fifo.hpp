#pragma once
#include <vector>
#include <stdexcept>

template<class T>
class fifo{
    /**
     * Simple ring-buffer for pointers
     * p_read = next index to read from
     * p_write = next index to write to
     *
     * Buffer is one element larger than queue capacity
     * => resolves disambiguity about being full or empty
     *
     * empty: p_read == p_write (next buffer to read from has not been written yet)
     * full: (p_write+1)%ringbuffer.size() == p_read
     *
     * The goal is for it to be thread safe when reading and writing happen seperately (mainly for writing in an interrupt and reading in normal code)
     */
private:
    std::vector<T> ringbuffer; 
    uint p_read;
    uint p_write;
public:
    fifo(uint size) : ringbuffer(size+1) {
        p_read = 0;
        p_write = 0;
    }

    inline bool is_empty() {
        return p_read == p_write;
    }

    inline bool is_full() {
        return (p_write+1)%ringbuffer.size() == p_read;
    }

    T pop() {
        if(is_empty())
            throw std::runtime_error("Attemptet pop on empty fifo");

        T retval = ringbuffer[p_read]; // retrieve value
        p_read = (p_read+1) % ringbuffer.size(); // increase read index -> only now can a new element be written to the fifo
        return retval;
    }

    void push(T new_element) {
        if(is_full())
            throw std::runtime_error("Attemptet push to full fifo");

        ringbuffer[p_write] = new_element;
        p_write = (p_write+1) % ringbuffer.size();
    }

    void debug() {
        printf("fifp: r=%u w=%u e:%u f:%u\n", p_read, p_write, is_empty(), is_full());
    }
};
