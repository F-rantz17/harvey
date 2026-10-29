"""Fashion / beauty brand fit: accented names, department titles,
accent-safe email guesses, and Shopify Web Pixel ad detection."""
from harvey.collectors import people as P
from harvey.collectors.profile import ProfileCollector, META_PIXEL, GOOGLE_ADS
from harvey.integrations import email_finder as EF

# Shopify inlines its pixel list as escaped JSON, exactly like this.
SHOPIFY_PIXELS = r'''<script>webPixelsManagerAPI.load({webPixelsConfigList: [
{"id":"1","configuration":"{\"pixel_id\":\"231438098273774\",\"pixel_type\":\"facebook_pixel\",\"metaapp_system_user_token\":\"-\"}","type":"APP","apiClientId":2329312},
{"id":"2","configuration":"{\"pixelCode\":\"D04KVFJC77UA6FH8TJQ0\"}","type":"APP","apiClientId":4383523},
{"id":"3","configuration":"{\"tagID\":\"2612485360749\"}","type":"APP","apiClientId":3009811},
{"id":"4","configuration":"{\"accountID\":\"U5wy6h\"}","type":"APP","apiClientId":123074}
],isMerchantRequest: false})</script><script src="https://cdn.shopify.com/s/x.js"></script>'''

PC = ProfileCollector(state=None)


def card(name, title):
    return f'<div class="card"><h3>{name}</h3><p>{title}</p></div>'


def test_shopify_web_pixels_count_as_ads():
    assert PC._any(SHOPIFY_PIXELS, META_PIXEL)
    tech = PC.detect_tech(SHOPIFY_PIXELS)
    for name in ("Shopify", "Meta Pixel", "TikTok Pixel", "Pinterest Tag", "Klaviyo"):
        assert name in tech, name


def test_shopify_without_ad_apps_is_not_an_ad_signal():
    plain = '<script>webPixelsConfigList: [{"configuration":"{\\"shopID\\": \\"97515\\"}","apiClientId":3780451}]</script>'
    assert not PC._any(plain, META_PIXEL)
    assert "TikTok Pixel" not in PC.detect_tech(plain)


def test_inline_google_ads_conversion_id():
    assert PC._any("<script>gtag('config', 'AW-16555030441');</script>", GOOGLE_ADS)
    assert not PC._any("<p>Call us: AW-12 dispatch</p>", GOOGLE_ADS)


def test_accented_names_are_kept_with_their_spelling():
    for name in ("Nadège Pierre-Louis", "Renée Dupont", "Chloé Bastien", "Anaïs Joseph"):
        html = "<html><body>" + card(name, "Founder &amp; CEO") + "</body></html>"
        got = [p["full_name"] for p in P.find_people([("https://x.test/team", html)], "x.test", "X")]
        assert got == [name]


def test_director_of_marketing_is_a_department_not_another_company():
    html = "<html><body>" + card("Camille Ortiz", "Director of Marketing") + "</body></html>"
    got = P.find_people([("https://x.test/team", html)], "x.test", "X")
    assert [p["title"] for p in got] == ["Director of Marketing"]
    # A real other organisation is still rejected.
    assert P.title_names_other_org("Director of Acme Holdings", "x.test", "X")


def test_email_guesses_fold_accents():
    assert EF.build_email("{f}.{l}", "Nadège", "Pierre-Louis", "x.test") == "nadege.pierrelouis@x.test"
    assert EF.build_email("{f}", "Anaïs", "Joseph", "x.test") == "anais@x.test"


def _people(html, domain="brand.test", name="Brand"):
    return [(p["full_name"], p["title"]) for p in P.find_people([(f"https://{domain}/pages/about", html)], domain, name)]


def test_first_person_founder_intro():
    html = ("<html><body><main><h2>WHAT IS LOW TIDE?</h2><p>My name is Idris Okafor. I’m the founder and "
            "creative director of LOW TIDE, and I’m 24 years old as I write this.</p></main></body></html>")
    assert _people(html, "lowtide-studios.example", "Low Tide") == [("Idris Okafor", "Founder & Creative Director")]


def test_meet_our_founder_heading_then_bio_sentence():
    html = ("<html><body><main><h3>Meet Our Founder</h3><p>Selma Haddad is a second-generation Rhode Island "
            "designer and vintage dealer.</p></main></body></html>")
    assert _people(html, "relic.example", "Relic") == [("Selma Haddad", "Founder")]


def test_meet_the_founder_heading_then_name_heading():
    html = ("<html><body><main><p>meet the founder</p><h2>Maren Kelleher</h2><p>Born and raised in Boston, "
            "Maren Kelleher has always been passionate about design.</p></main></body></html>")
    assert _people(html, "patchwork.example", "Patchwork") == [("Maren Kelleher", "Founder")]


def test_is_the_founder_of_this_brand_only():
    mine = "<html><body><p>Odessa Vance is the Founder of Vance Studio, an apparel brand.</p></body></html>"
    assert ("Odessa Vance", "Founder") in _people(mine, "vancestudio.example", "Vance Studio")
    other = "<html><body><p>Jane Roe is the Founder of Acme Holdings, a client of ours.</p></body></html>"
    assert _people(other, "vancestudio.example", "Vance Studio") == []


def test_my_name_without_a_role_is_not_a_contact():
    html = "<html><body><p>My name is Jordan Price. I love these jeans and wear them daily.</p></body></html>"
    assert _people(html) == []


def test_meet_our_founder_with_accented_name():
    html = ("<html><body><main><h3>Meet Our Founder</h3><p>Nadège Pierre-Louis is a Haitian-American "
            "chemist and formulator.</p></main></body></html>")
    assert _people(html, "lumiere.example", "Lumiere") == [("Nadège Pierre-Louis", "Founder")]
