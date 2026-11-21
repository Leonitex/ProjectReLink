// Conservative, opt-in early reclaim of idle spare Vulkan images on low-VRAM cards.
// Only spare images that have been unused for at least 60 presents qualify.
#pragma once
#include <cstdint>

namespace mkwvk::spare_pressure {
constexpr bool release_idle(std::uint64_t used, std::uint64_t allowed,
                            int percent, std::uint64_t age) noexcept {
    return percent > 0 && percent < 100 && allowed >= 100 && age >= 60 &&
           used >= (allowed / 100) * static_cast<unsigned>(percent);
}
}  // namespace mkwvk::spare_pressure
