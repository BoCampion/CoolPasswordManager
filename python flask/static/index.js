function showDetails(site, username, password) {
    document.getElementById('entryDetails').style.display = 'block';
    document.getElementById('detailSite').textContent = site;
    document.getElementById('detailUsername').textContent = username;
    document.getElementById('detailPassword').textContent = password;
}

function togglePopup() {
    const popup = document.getElementById('popupForm');
    popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
}

function closeDetails() {
    document.getElementById('entryDetails').style.display = 'none';
}

