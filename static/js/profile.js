/**
 * XploreElite - Profile Management Controller
 */

let isEditMode = false;
let originalProfile = null;

document.addEventListener('DOMContentLoaded', async () => {
  await loadProfile();
  setupProfileHandlers();
});

async function loadProfile() {
  try {
    const profile = await TourismAPI.getProfile();
    originalProfile = { ...profile };

    // Update left card
    document.getElementById('profileDisplayName').textContent = profile.fullName;
    document.getElementById('profileDisplayRole').textContent = profile.role;
    document.getElementById('profileDisplayEmail').textContent = profile.email;
    document.getElementById('profileDisplayPhone').textContent = profile.phone;
    document.getElementById('profileDisplayCompany').textContent = profile.companyName;

    // Update header profile display (phone, email, name)
    if (typeof syncHeaderProfileUI === 'function') {
      syncHeaderProfileUI(profile);
    } else {
      document.querySelectorAll('.user-profile-menu .user-name').forEach(el => {
        el.textContent = profile.fullName;
      });
    }

    // Update form fields
    document.getElementById('profFullName').value = profile.fullName;
    document.getElementById('profEmail').value = profile.email;
    document.getElementById('profPhone').value = profile.phone;
    document.getElementById('profCompany').value = profile.companyName;
    document.getElementById('profRole').value = profile.role;

    // Update metadata
    document.getElementById('profLastLogin').textContent = profile.lastLogin;
    document.getElementById('profCreated').textContent = profile.accountCreated;
    document.getElementById('profAccessLevel').textContent = profile.accessLevel;

    setFormFieldsDisabled(true);
  } catch (error) {
    console.error('Failed to load profile:', error);
    showToast('Failed to load profile details.', 'danger');
  }
}

function setFormFieldsDisabled(disabled) {
  const fields = ['profFullName', 'profEmail', 'profPhone', 'profCompany', 'profRole'];
  fields.forEach(fId => {
    const el = document.getElementById(fId);
    if (el) el.disabled = disabled;
  });

  const editBtn = document.getElementById('editProfileToggleBtn');
  const saveBtn = document.getElementById('saveProfileBtn');
  const cancelBtn = document.getElementById('cancelProfileBtn');

  if (disabled) {
    if (editBtn) editBtn.style.display = 'inline-flex';
    if (saveBtn) saveBtn.style.display = 'none';
    if (cancelBtn) cancelBtn.style.display = 'none';
  } else {
    if (editBtn) editBtn.style.display = 'none';
    if (saveBtn) saveBtn.style.display = 'inline-flex';
    if (cancelBtn) cancelBtn.style.display = 'inline-flex';
  }
}

function setupProfileHandlers() {
  const editBtn = document.getElementById('editProfileToggleBtn');
  const cancelBtn = document.getElementById('cancelProfileBtn');
  const profileForm = document.getElementById('profileForm');

  if (editBtn) {
    editBtn.addEventListener('click', () => {
      isEditMode = true;
      setFormFieldsDisabled(false);
      document.getElementById('profFullName').focus();
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      isEditMode = false;
      // Revert values
      document.getElementById('profFullName').value = originalProfile.fullName;
      document.getElementById('profEmail').value = originalProfile.email;
      document.getElementById('profPhone').value = originalProfile.phone;
      document.getElementById('profCompany').value = originalProfile.companyName;
      document.getElementById('profRole').value = originalProfile.role;
      setFormFieldsDisabled(true);
    });
  }

  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fullName = document.getElementById('profFullName').value.trim();
      const email = document.getElementById('profEmail').value.trim();
      const phone = document.getElementById('profPhone').value.trim();
      const companyName = document.getElementById('profCompany').value.trim();
      const role = document.getElementById('profRole').value.trim();

      if (!fullName || !email) {
        showToast('Full name and email are mandatory.', 'danger');
        return;
      }

      const saveBtn = document.getElementById('saveProfileBtn');
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

      try {
        const updated = await TourismAPI.updateProfile({
          ...originalProfile,
          username: fullName,
          fullName: fullName,
          email,
          phone,
          companyName,
          role
        });

        originalProfile = { ...updated };
        isEditMode = false;
        setFormFieldsDisabled(true);

        // Update left card
        document.getElementById('profileDisplayName').textContent = updated.fullName;
        document.getElementById('profileDisplayRole').textContent = updated.role;
        document.getElementById('profileDisplayEmail').textContent = updated.email;
        document.getElementById('profileDisplayPhone').textContent = updated.phone;
        document.getElementById('profileDisplayCompany').textContent = updated.companyName;

        // Update form inputs to match saved data
        document.getElementById('profFullName').value = updated.fullName;
        document.getElementById('profEmail').value = updated.email;
        document.getElementById('profPhone').value = updated.phone;
        document.getElementById('profCompany').value = updated.companyName;
        document.getElementById('profRole').value = updated.role;

        // Update header profile display across page (phone, email, name)
        if (typeof syncHeaderProfileUI === 'function') {
          syncHeaderProfileUI(updated);
        } else {
          document.querySelectorAll('.user-profile-menu .user-name').forEach(el => {
            el.textContent = updated.fullName;
          });
        }
        localStorage.setItem('auth_user_name', updated.fullName);
        localStorage.setItem('user_profile', JSON.stringify(updated));

        showToast('Profile information updated successfully!', 'success');
      } catch (err) {
        showToast('Failed to update profile: ' + err.message, 'danger');
      } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fa-solid fa-check"></i> <span>Save Changes</span>';
      }
    });
  }
}
