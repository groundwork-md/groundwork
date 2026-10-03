# groundwork base layer. Every recipe lives in `groundwork.just`, which private layers import via a
# `.groundwork` symlink — so the base runs its own mechanism exactly the way a layer does, rather than
# carrying a second copy that could drift.

import 'groundwork.just'
