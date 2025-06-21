let allChecked;

document.addEventListener("DOMContentLoaded", () => {
  const showFilterButton = document.getElementById("show-filter").addEventListener("click", toggleFilter);
  const closeFilterButton = document.getElementById("close-filter").addEventListener("click", toggleFilter);
  let filterForm = document.getElementById('filter').addEventListener("submit", submitAllCities)

  const citiesList = document.getElementsByName("cit");
  checkAll(citiesList);

  allChecked = document.getElementById('all-cities');
  allChecked.addEventListener("change", () => toggleAll(citiesList));

  for (const city of citiesList) {
    city.addEventListener("change", () => checkAll(citiesList));
  }
})


function toggleFilter() {
  let translucent = document.getElementById("translucent").style.display;
  let filter = document.getElementById("filter").style.display;

  let filterStatus;
  switch (translucent) {
    case "none":
    case "":
    case null:
    case undefined:
      filterStatus = false;
      break;
    default:
      filterStatus = true;
  }
  switch (filter) {
    case "none":
    case "":
    case null:
    case undefined:
      filterStatus = false;
      break;
    default:
      filterStatus = true;
  }

  if (filterStatus) {
    document.getElementById("translucent").style.display = "none";
    document.getElementById("filter").style.display = "none";
  } else {
    document.getElementById("translucent").style.display = "block";
    document.getElementById("filter").style.display = "block";
  };
}


// ensure that the filter is displayed correctly on window resizes
window.addEventListener("resize", () => {
  let windowWidth = window.innerWidth;
  if (windowWidth > 1399) {
    document.getElementById("translucent").style.display = "block";
    document.getElementById("filter").style.display = "block";
  } else {
    document.getElementById("translucent").style.display = "none";
    document.getElementById("filter").style.display = "none";
  };
})

function checkAll(citiesList) {
  let all = true;
  let allCitiesCheckbox = document.getElementById("all-cities");
  for (let i = 1; i < citiesList.length; i++) {
    if (!citiesList[i].checked) { all = false };
    allCitiesCheckbox.checked = false;
  };
  if (all == true) {
    allCitiesCheckbox.checked = true;
  };

  // let submitBtnDisabled = false;
  let submitBtn = document.getElementById("filterSubmit");
  for (let i = 1; i < citiesList.length; i++) {
    if (citiesList[i].checked) {
      submitBtn.disabled = false;
      // submitBtn.style.backgroundColor = "var(--olive)";
      submitBtn.className = "active-button"
      return;
    }
  };
  submitBtn.disabled = true;
  // submitBtn.style.backgroundColor = "var(--tan)";
  submitBtn.className = "inactive-button"
};

function toggleAll(citiesList) {
  if (allChecked.checked) {
    citiesList.forEach(cb => cb.checked = true);
  } else {
    citiesList.forEach(cb => cb.checked = false);
  }
}

function submitAllCities() {
  const checkboxes = document.getElementsByName('cit');
  const allChecked = Array.from(checkboxes).every(cb => cb.checked);
  const allCheckbox = document.getElementById('all-cities');

  if (allChecked) {
    checkboxes.forEach(cb => cb.checked = false);
    document.getElementById('all-cities').checked = true;
  };

  const allCats = document.getElementById('categories')
  console.log(allCats.value)
}

