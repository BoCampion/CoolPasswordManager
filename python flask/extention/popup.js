document.addEventListener('DOMContentLoaded', () => {
  const userInfo = document.getElementById('user-info');
  const form = document.getElementById('password-form');
  const message = document.getElementById('message');

  // Check if user is logged in
  fetch('http://127.0.0.1:5000/api/user', {
      method: 'GET',
      credentials: 'include'  // VERY IMPORTANT: allows cookies to be sent
  })
  .then(response => {
      if (!response.ok) {
          throw new Error("Failed to fetch");
      }
      return response.json();
  })
  .then(data => {
      if (data.logged_in) {
          userInfo.textContent = `Logged in as: ${data.username}`;
          userInfo.style.color = 'green';
          form.style.display = 'block';
          message.textContent = '';
      } else {
          userInfo.textContent = 'You are not logged in.';
          userInfo.style.color = 'red';
          form.style.display = 'none';
          message.textContent = 'Please log in to use the extension.';
      }
  })
  .catch(err => {
      console.error('Fetch error:', err);
      userInfo.textContent = 'Server unavailable.';
      userInfo.style.color = 'red';
      form.style.display = 'none';
      message.textContent = 'Could not connect to the backend.';
  });

  // Handle credential form submission
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const site = document.getElementById('site').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    fetch('http://127.0.0.1:5000/add', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `site=${encodeURIComponent(site)}&username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            message.textContent = 'Credential added successfully!';
            message.style.color = 'green';
            form.reset();
        } else {
            message.textContent = 'Please log in first.';
            message.style.color = 'red';
        }
    })
    .catch(err => {
        console.error('Add credential error:', err);
        message.textContent = 'Failed to add credential.';
        message.style.color = 'red';
    });
});
});
