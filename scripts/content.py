"""Shared presentation helpers for the website/PDF content source."""
def resume_summary(profile):
    return profile['pdf_summary'].format(industries=', '.join(profile['industries']))

def resume_skill_text(profile, selection):
    group = next(group for group in profile['skills'] if group['theme'] == selection['theme'])
    items = {item['name']: item for item in group['items']}
    grouped = {}
    for selected in selection['items']:
        item = items[selected['name']]
        grouped.setdefault(item['level'], []).append(selected.get('label', item['name']))
    return '; '.join(', '.join(names) + ' (' + level + ')' for level, names in grouped.items())
