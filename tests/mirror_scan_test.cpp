#include "../gpu/vk/mirror_scan.h"
#include <cassert>
#include <cstdint>
#include <vector>
#include <algorithm>

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

    // Randomized semantic regression: 10,000 pool offsets, lengths and
    // page-generation patterns. Dirty pages must match the old algorithm.
    std::uint32_t seed = 0xC0FFEEu;
    auto rand32 = [&]() { seed = seed * 1664525u + 1013904223u; return seed; };
    constexpr std::uint64_t total_pages = 4096, region_pages = 512;
    for (int trial = 0; trial < 10000; ++trial) {
        const auto first = rand32() % total_pages;
        const auto length = 1 + rand32() % (total_pages - first);
        const auto last = first + length;
        const std::uint32_t synced = 10;
        std::vector<std::uint32_t> page_gen(total_pages, 1), region_gen(total_pages / region_pages, 1);
        for (int n = 0; n < 100; ++n) {
            const auto pg = rand32() % total_pages;
            const auto gen = rand32() % 20;
            page_gen[pg] = gen;
            region_gen[pg / region_pages] = std::max(region_gen[pg / region_pages], gen);
        }
        std::vector<std::uint64_t> dirty_original, dirty_optimized;
        for (auto pg = first; pg < last;) {
            if (pg % region_pages == 0 && region_gen[pg / region_pages] <= synced) {
                pg += region_pages;
                continue;
            }
            if (page_gen[pg] > synced) dirty_original.push_back(pg);
            ++pg;
        }
        for (auto pg = first; pg < last;) {
            if (region_gen[pg / region_pages] <= synced) {
                pg = after_clean_region(pg, last, region_pages);
                continue;
            }
            if (page_gen[pg] > synced) dirty_optimized.push_back(pg);
            ++pg;
        }
        assert(dirty_original == dirty_optimized);
    }
    return 0;
}
