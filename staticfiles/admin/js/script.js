/**
 * GymWord Admin Panel JavaScript
 */

// Image Preview
function previewImage(input, previewId) {
  if (input.files && input.files[0]) {
    const reader = new FileReader()

    reader.onload = (e) => {
      const preview = document.getElementById(previewId)
      if (preview) {
        preview.src = e.target.result
        preview.style.display = "block"
      }
    }

    reader.readAsDataURL(input.files[0])
  }
}

// Dynamic Form Fields
function addDynamicField(containerId, fieldName) {
  const container = document.getElementById(containerId)
  if (!container) return

  const fieldCount = container.children.length
  const fieldDiv = document.createElement("div")
  fieldDiv.className = "dynamic-form-field"

  fieldDiv.innerHTML = `
        <input type="text" class="form-control" name="${fieldName}[]" required>
        <button type="button" class="btn btn-danger remove-field-btn">
            <i class="fas fa-times"></i>
        </button>
    `

  container.appendChild(fieldDiv)

  // Add event listener to remove button
  const removeBtn = fieldDiv.querySelector(".remove-field-btn")
  if (removeBtn) {
    removeBtn.addEventListener("click", () => {
      container.removeChild(fieldDiv)
    })
  }
}

// Initialize dynamic fields
document.addEventListener("DOMContentLoaded", () => {
  // Add event listeners to all add field buttons
  const addFieldBtns = document.querySelectorAll(".add-field-btn")
  addFieldBtns.forEach((btn) => {
    const containerId = btn.getAttribute("data-container")
    const fieldName = btn.getAttribute("data-field-name")

    if (containerId && fieldName) {
      btn.addEventListener("click", () => {
        addDynamicField(containerId, fieldName)
      })
    }
  })

  // Add event listeners to all remove field buttons
  const removeFieldBtns = document.querySelectorAll(".remove-field-btn")
  removeFieldBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const fieldDiv = btn.closest(".dynamic-form-field")
      if (fieldDiv && fieldDiv.parentNode) {
        fieldDiv.parentNode.removeChild(fieldDiv)
      }
    })
  })

  // Add event listeners to all image inputs
  const imageInputs = document.querySelectorAll(".image-input")
  imageInputs.forEach((input) => {
    const previewId = input.getAttribute("data-preview")
    if (previewId) {
      input.addEventListener("change", function () {
        previewImage(this, previewId)
      })
    }
  })

  // Initialize datepickers
  const datepickers = document.querySelectorAll(".datepicker")
  if (datepickers.length > 0 && typeof flatpickr === "function") {
    datepickers.forEach((picker) => {
      flatpickr(picker, {
        dateFormat: "Y-m-d",
      })
    })
  }

  // Initialize select2
  const select2Inputs = document.querySelectorAll(".select2")
  if (select2Inputs.length > 0 && typeof $.fn.select2 === "function") {
    $(select2Inputs).select2({
      theme: "bootstrap4",
    })
  }

  // Initialize CKEditor
  const richTextEditors = document.querySelectorAll(".rich-text-editor")
  if (richTextEditors.length > 0 && typeof ClassicEditor === "function") {
    richTextEditors.forEach((editor) => {
      ClassicEditor.create(editor).catch((error) => {
        console.error(error)
      })
    })
  }

  // Confirm delete
  const deleteButtons = document.querySelectorAll(".btn-delete")
  deleteButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      if (!confirm("Are you sure you want to delete this item? This action cannot be undone.")) {
        e.preventDefault()
      }
    })
  })

  // Toggle password visibility
  const togglePasswordButtons = document.querySelectorAll(".toggle-password")
  togglePasswordButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const passwordInput = document.getElementById(btn.getAttribute("data-target"))
      if (passwordInput) {
        const type = passwordInput.getAttribute("type") === "password" ? "text" : "password"
        passwordInput.setAttribute("type", type)

        // Toggle icon
        const icon = btn.querySelector("i")
        if (icon) {
          icon.classList.toggle("fa-eye")
          icon.classList.toggle("fa-eye-slash")
        }
      }
    })
  })
})

// AJAX Search
function ajaxSearch(url, query, resultContainerId) {
  const container = document.getElementById(resultContainerId)
  if (!container) return

  // Show loading indicator
  container.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</div>'

  fetch(`${url}?search=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      container.innerHTML = ""

      if (data.length === 0) {
        container.innerHTML = '<div class="text-center">No results found</div>'
        return
      }

      // Create result items
      data.forEach((item) => {
        const resultItem = document.createElement("div")
        resultItem.className = "search-result-item"
        resultItem.innerHTML = `
                    <div class="search-result-item-content">
                        <h5>${item.name || item.title || item.username}</h5>
                        <p>${item.description || item.email || ""}</p>
                    </div>
                    <div class="search-result-item-actions">
                        <button type="button" class="btn btn-sm btn-primary select-result" data-id="${item.id}" data-name="${item.name || item.title || item.username}">
                            Select
                        </button>
                    </div>
                `
        container.appendChild(resultItem)

        // Add event listener to select button
        const selectBtn = resultItem.querySelector(".select-result")
        if (selectBtn) {
          selectBtn.addEventListener("click", function () {
            const id = this.getAttribute("data-id")
            const name = this.getAttribute("data-name")

            // Find the hidden input and visible input
            const hiddenInput = document.querySelector(`[data-search-for="${resultContainerId}"]`)
            const visibleInput = document.querySelector(`[data-search-display="${resultContainerId}"]`)

            if (hiddenInput) hiddenInput.value = id
            if (visibleInput) visibleInput.value = name

            // Hide results
            container.innerHTML = ""
          })
        }
      })
    })
    .catch((error) => {
      console.error("Error fetching search results:", error)
      container.innerHTML = '<div class="text-center text-danger">Error fetching results</div>'
    })
}

// Initialize AJAX search
document.addEventListener("DOMContentLoaded", () => {
  const searchInputs = document.querySelectorAll("[data-search-url]")
  searchInputs.forEach((input) => {
    const url = input.getAttribute("data-search-url")
    const resultContainerId = input.getAttribute("data-search-results")

    if (url && resultContainerId) {
      // Debounce function to prevent too many requests
      let debounceTimer

      input.addEventListener("input", function () {
        clearTimeout(debounceTimer)
        const query = this.value.trim()

        if (query.length < 2) {
          document.getElementById(resultContainerId).innerHTML = ""
          return
        }

        debounceTimer = setTimeout(() => {
          ajaxSearch(url, query, resultContainerId)
        }, 300)
      })
    }
  })
})

