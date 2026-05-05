from flask import flash, redirect, url_for

from CTFd.admin import admin
from CTFd.models import Users
from CTFd.utils.decorators import admins_only
from CTFd.utils.email import winner_certificate
from CTFd.utils.scores import get_standings
from CTFd.cache import cache


@admin.route("/admin/certificates/send", methods=["POST"])
@admins_only
def send_winner_certificates():
    try:
        cache.delete_memoized(get_standings)
        top3 = get_standings(count=3, admin=True)
    except Exception as e:
        flash(f"Error fetching standings: {e}", "danger")
        return redirect(url_for("admin.config") + "#certificates")

    if not top3:
        flash("No standings found. Has anyone scored yet?", "warning")
        return redirect(url_for("admin.config") + "#certificates")

    for rank, standing in enumerate(top3, start=1):
        try:
            user = Users.query.get(standing.account_id)
        except Exception as e:
            flash(f"Rank {rank}: DB error — {e}", "danger")
            continue

        if not user or not user.email:
            flash(f"Rank {rank} ({standing.name}): no email found.", "warning")
            continue

        try:
            success, message = winner_certificate(
                addr=user.email,
                name=standing.name,
                rank=rank,
                score=standing.score,
            )
        except Exception as e:
            flash(f"Rank {rank} ({standing.name}): unexpected error — {e}", "danger")
            continue

        if success:
            flash(f"Rank {rank} ({standing.name}): certificate sent", "success")
        else:
            flash(f"Rank {rank} ({standing.name}): failed — {message}", "danger")

    return redirect(url_for("admin.config") + "#certificates")