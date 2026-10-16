"""Small, code-native decorative icons shared by profile sections."""
PATHS={
 'person':'<circle cx="12" cy="7" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3H4z"/>',
 'briefcase':'<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V3h8v4M3 11h18M9 10v4h6v-4"/>',
 'gear':'<path d="M9 3h6l1 4 4 1v6l-4 1-1 4H9l-1-4-4-1V8l4-1z"/><circle cx="12" cy="11" r="3"/>',
 'server':'<rect x="3" y="3" width="18" height="8" rx="2"/><rect x="3" y="13" width="18" height="8" rx="2"/><path d="M7 7h.1M7 17h.1M11 7h6m-6 10h6"/>',
 'users':'<circle cx="10" cy="7" r="3"/><path d="M3 22v-4a7 7 0 0 1 14 0v4M17 4a3 3 0 0 1 0 6m2 4a5 5 0 0 1 3 5v3"/>',
 'cloud':'<path d="M7 18H6a4 4 0 0 1-.5-8A6.5 6.5 0 0 1 18 8a5 5 0 0 1 0 10H7z"/>',
 'layers':'<path d="m12 2 10 5-10 5L2 7l10-5zM2 12l10 5 10-5M2 17l10 5 10-5"/>',
 'chart':'<rect x="4" y="12" width="3" height="9" rx="1"/><rect x="10.5" y="7" width="3" height="14" rx="1"/><rect x="17" y="3" width="3" height="18" rx="1"/>',
 'target':'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="m12 12 9-9M17 3h4v4"/>',
 'graduation':'<path d="m2 8 10-5 10 5-10 5L2 8zM6 10v7c4 4 8 4 12 0v-7M22 8v9"/>',
 'language':'<path d="M3 5h12M9 2v3M5 5c1 7 5 10 9 12M13 5c-1 7-5 10-9 12M13 22l4-10 5 10m-7-4h5"/>'
}
def icon(name, css='section-icon'):
    return f'<span class="{css}" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg></span>'
def orbits():
    return '<div class="section-orbits" aria-hidden="true"><span class="orbit-globe"></span><span class="orbit-ring"></span><span class="orbit-ring ring-two"></span><i></i><i></i><i></i></div>'
