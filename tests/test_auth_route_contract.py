from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_auth_entry_routes_exist():
    for route in (
        "website/app/login/page.tsx",
        "website/app/signup/page.tsx",
        "website/app/register/page.tsx",
        "website/app/auth/callback/page.tsx",
        "website/app/api/auth/signup/start/route.ts",
        "website/app/api/auth/signup/verify/route.ts",
        "website/app/api/auth/signin/start/route.ts",
        "website/app/api/auth/signin/verify/route.ts",
        "website/app/api/auth/sync/route.ts",
    ):
        assert (ROOT / route).is_file(), route


def test_post_auth_redirect_rejects_protocol_relative_urls():
    source = (ROOT / "website/lib/auth.ts").read_text()
    assert "!returnTo.startsWith('//')" in source
    assert "!returnTo.includes('\\\\')" in source
