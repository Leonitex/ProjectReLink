#include "../gpu/vk/mirror_scan.h"
#include <cassert>
#include <cstdint>

int main() {
    using mkwvk::mirror_scan::after_clean_region;
    constexpr std::uint64_t region = 512; // 512 * 4096 B = 2 MiB
    static_assert(after_clean_region(0, 2048, region) == 512);
    static_assert(after_clean_region(1, 2048, region) == 512);
    static_assert(after_clean_region(511, 2048, region) == 512);
    static_assert(after_clean_region(512, 2048, region) == 1024);
    static_assert(after_clean_region(777, 2048, region) == 1024);
    static_assert(after_clean_region(800, 900, region) == 900);
    static_assert(after_clean_region(1, 12, region) == 12);
    static_assert(after_clean_region(1023, 1023, region) == 1023);
    static_assert(after_clean_region(1025, 1024, region) == 1025);
    static_assert(after_clean_region(10, 20, 0) == 10);

    // Exact dirty-page equivalence: skip only regions whose newest page
    // generation is known to be no newer than the mirrored generation.
    const std::uint32_t latest[] = {1, 2, 9, 1, 4, 2, 1};
    constexpr std::uint64_t size = 4; // smaller regions for a readable test
    const std::uint64_t lo = 3, hi = 25;
    constexpr std::uint32_t mirror_gen = 3;
    std::uint64_t dirty_original = 0, dirty_new = 0;
    int checks_original = 0, checks_new = 0;
    for (auto page = lo; page < hi; ++page) {
        ++checks_original;
        if (latest[page / size] > mirror_gen) dirty_original |= 1ull << page;
    }
    for (auto page = lo; page < hi;) {
        if (latest[page / size] <= mirror_gen) {
            page = after_clean_region(page, hi, size);
            continue;
        }
        ++checks_new;
        dirty_new |= 1ull << page;
        ++page;
    }
    assert(dirty_original == dirty_new);
    assert(checks_new < checks_original);
    return 0;
}
