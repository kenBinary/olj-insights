from bs4 import BeautifulSoup


def extract_skills_from_html(raw_html):
    # If the HTML string comes from a CSV/text dump with double escaped quotes (""),
    # we clean it up so BeautifulSoup can parse the attributes perfectly.
    cleaned_html = raw_html.replace('""', '"')

    # Parse the HTML
    soup = BeautifulSoup(cleaned_html, "html.parser")

    # 1. Find the <strong> or text element that contains "SKILL REQUIREMENT"
    skill_label = soup.find(
        "strong", string=lambda text: text and "SKILL REQUIREMENT" in text.upper()
    )

    # If the section does not exist, return an empty string
    if not skill_label:
        return ""

    # 2. Navigate up to the card header
    card_header = skill_label.find_parent("div", class_="card-header")
    if not card_header:
        return ""

    # 3. Navigate to the sibling card-body which contains the actual skills
    card_body = card_header.find_next_sibling("div", class_="card-body")
    if not card_body:
        return ""

    # 4. Extract all the <a> tags with the class "card-worker-topskill"
    skill_tags = card_body.find_all("a", class_="card-worker-topskill")

    # 5. Get the text from each tag, strip whitespace, and join them with a comma
    skills = [tag.get_text(strip=True) for tag in skill_tags]

    return ";".join(skills)


# ==========================================
# Example Usage with your provided HTML:
# ==========================================

if __name__ == "__main__":
    html_content = """
    
    """

    # Test when the section exists
    result = extract_skills_from_html(html_content)
    print("Skills found:", result)
