from bs4 import BeautifulSoup


def extract_date_updated(soup):
    # 1. Find the text "DATE UPDATED"
    date_label = soup.find(string=lambda text: text and "DATE UPDATED" in text.upper())

    if not date_label:
        return ""

    # 2. Navigate up to its parent <h3> tag
    h3_tag = date_label.find_parent("h3")
    if not h3_tag:
        return ""

    # 3. The date text is inside the very next <p> tag
    p_tag = h3_tag.find_next_sibling("p")
    if not p_tag:
        return ""

    # 4. Return the cleaned text
    return p_tag.get_text(strip=True)


# ==========================================
# Example Usage with your combined raw HTML:
# ==========================================

raw_html = """
<div class="col-lg-3 col-md-6">
    <dl class="row no-gutters">
        <dt class="col-auto">
            <img src="/images/icon-date.jpg" alt="">
        </dt>
        <dd class="col-auto">
            <h3 class="fs-12 mb-0">DATE UPDATED</h3>
            <p class="fs-18"> Sep 6, 2025 </p>
        </dd>
    </dl>
</div>

<div class="row justify-content-center">
    <div class="col-12">
        <div class="card card-jobseeker card-worker card-job-post shadow-sm mb-40">
            <div class="card-header fs-18">
                <i class="icon icon-selection"></i> <strong>SKILL REQUIREMENT</strong>
            </div>
            <div class="card-body">
                <dl class="card-worker-dl mb-4">
                    <dd>
                        <a href="..." class="card-worker-topskill">API Development</a>
                        <a href="..." class="card-worker-topskill">Stripe Api</a>
                        <a href="..." class="card-worker-topskill">API Integration</a>
                    </dd>
                </dl>
            </div>
        </div>
    </div>
</div>
"""

soup = BeautifulSoup(raw_html, "html.parser")
date_updated = extract_date_updated(soup)
print(f"Date Updated: '{date_updated}'")
