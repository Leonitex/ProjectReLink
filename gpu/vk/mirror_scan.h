// Skip clean 2 MiB mirror-sync regions even when a buffer starts or ends
// between region boundaries. The caller must only skip when the region's
// newest write generation is <= the mirror's synchronized generation.
#pragma once
#include <cstdint>

namespace mkwvk::mirror_scan {

// page and end_page are page numbers, with end_page exclusive.
// Advance only to the next region or the end of this pool, whichever comes
// first. The caller owns the dirty-region check; this helper never skips a
// potentially dirty page on its own.
constexpr std::uint64_t after_clean_region(std::uint64_t page,
                                           std::uint64_t end_page,
                                           std::uint64_t region_pages) noexcept {
    if (!region_pages || page >= end_page) return page;
    const auto to_boundary = region_pages - page % region_pages;
    const auto remaining = end_page - page;
    return page + (to_boundary < remaining ? to_boundary : remaining);
}

} // namespace mkwvk::mirror_scan
