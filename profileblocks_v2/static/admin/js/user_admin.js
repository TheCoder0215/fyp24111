// static/admin/js/user_admin.js
document.addEventListener('DOMContentLoaded', function() {
    var userTypeSelect = document.querySelector('select[name="user_type"]');
    var institutionTypeDiv = document.querySelector('div.field-institution_type');

    function toggleInstitutionType() {
        if (userTypeSelect.value === 'institution') {
            institutionTypeDiv.style.display = 'block';
        } else {
            institutionTypeDiv.style.display = 'none';
        }
    }

    if (userTypeSelect) {
        userTypeSelect.addEventListener('change', toggleInstitutionType);
        toggleInstitutionType(); // Initial state
    }
});