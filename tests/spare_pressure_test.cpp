#include "../gpu/vk/spare_pressure.h"
#include <cassert>

int main() {
    using mkwvk::spare_pressure::release_idle;
    assert(!release_idle(3500, 4000, 0, 600));    // disabled by default
    assert(!release_idle(3500, 4000, 85, 59));    // recently retired: reusable
    assert(release_idle(3500, 4000, 85, 60));     // old and above soft threshold
    assert(!release_idle(3300, 4000, 85, 600));   // below pressure threshold
    assert(!release_idle(3900, 0, 85, 600));      // missing budget
    assert(!release_idle(3900, 4000, 100, 600));  // invalid threshold
    assert(release_idle(3400, 4000, 85, 120));    // boundary included
    return 0;
}
