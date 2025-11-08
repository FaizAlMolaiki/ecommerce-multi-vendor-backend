// Users form enhancements: toggle Delivery Data card and ensure multipart form when needed

(function() {
  function byId(id) { return document.getElementById(id); }
  function q(sel, root) { return (root || document).querySelector(sel); }

  function setFormMultipartIfNeeded() {
    const form = q('form.needs-validation');
    if (!form) return;
    const hasDeliveryFiles = !!(byId('delivery_id_card_image') || byId('delivery_driver_license_image'));
    const hasStaffFiles = !!(byId('staff_id_card_image') || byId('staff_resume_cv'));
    const deliveryCardVisible = !byId('delivery-card')?.classList.contains('d-none');
    const staffCardVisible = !byId('staff-card')?.classList.contains('d-none');
    if (hasDeliveryFiles || hasStaffFiles || deliveryCardVisible || staffCardVisible) {
      form.setAttribute('enctype', 'multipart/form-data');
    }
  }

  function toggleDeliveryCard(checked) {
    const card = byId('delivery-card');
    if (!card) return;
    if (checked) {
      card.classList.remove('d-none');
    } else {
      card.classList.add('d-none');
    }
    setFormMultipartIfNeeded();
  }

  function toggleStaffCard(checked) {
    const card = byId('staff-card');
    if (!card) return;
    if (checked) {
      card.classList.remove('d-none');
    } else {
      card.classList.add('d-none');
    }
    setFormMultipartIfNeeded();
  }

  function initDeliveryToggle() {
    const deliveryCheckbox = byId('id_is_delivery');
    if (!deliveryCheckbox) return;

    // Initial state
    toggleDeliveryCard(!!deliveryCheckbox.checked);

    // Listen for changes
    deliveryCheckbox.addEventListener('change', function() {
      toggleDeliveryCard(!!this.checked);
    });

    // If file inputs change, ensure multipart
    ['delivery_id_card_image', 'delivery_driver_license_image'].forEach(id => {
      const el = byId(id);
      if (el) {
        el.addEventListener('change', setFormMultipartIfNeeded);
      }
    });
  }

  function initStaffToggle() {
    const staffCheckbox = byId('id_is_staff');
    if (!staffCheckbox) return;

    // Initial state
    toggleStaffCard(!!staffCheckbox.checked);

    // Listen for changes
    staffCheckbox.addEventListener('change', function() {
      toggleStaffCard(!!this.checked);
    });

    // If file inputs change, ensure multipart
    ['staff_id_card_image', 'staff_resume_cv'].forEach(id => {
      const el = byId(id);
      if (el) {
        el.addEventListener('change', setFormMultipartIfNeeded);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    initDeliveryToggle();
    initStaffToggle();
  });
})();

