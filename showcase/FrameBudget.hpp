#pragma once
#include <chrono>
#include <thread>

// Always active, including direct executable launches and offline captures.
// Vsync alone does not cap a headless context or a high-refresh display.
class FrameBudget {
    std::chrono::steady_clock::time_point start_ = std::chrono::steady_clock::now();
public:
    ~FrameBudget() { std::this_thread::sleep_until(start_ + std::chrono::milliseconds(34)); }
};
