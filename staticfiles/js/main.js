document.addEventListener("DOMContentLoaded", () => {
  // Initialize all interactive elements
  initializeNavigation()
  initializeScrollEffects()
  initializeFAQ()

  // Add event listeners for forms
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", validateForm)
  })

  // Initialize sliders if they exist
  if (document.querySelector(".testimonial-slider")) {
    initializeTestimonialSlider()
  }

  // Initialize plan tabs if they exist
  if (document.querySelector(".plan-tabs")) {
    initializePlanTabs()
  }
})

// Navigation functions
function initializeNavigation() {
  // Mobile navigation toggle
  const navToggle = document.getElementById("navToggle")
  const navLinks = document.getElementById("navLinks")

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      navLinks.classList.toggle("show")

      // Toggle hamburger animation
      const spans = navToggle.querySelectorAll("span")
      spans.forEach((span) => span.classList.toggle("active"))
    })
  }

  // Close navigation when clicking outside
  document.addEventListener("click", (event) => {
    if (
      navLinks &&
      navLinks.classList.contains("show") &&
      !event.target.closest(".nav-toggle") &&
      !event.target.closest(".nav-links")
    ) {
      navLinks.classList.remove("show")
    }
  })

  // Dropdown functionality
  const dropdownToggles = document.querySelectorAll(".dropdown-toggle")
  dropdownToggles.forEach((toggle) => {
    toggle.addEventListener("click", function (e) {
      e.preventDefault()
      const dropdown = this.nextElementSibling
      dropdown.classList.toggle("show")

      // Close other dropdowns
      dropdownToggles.forEach((otherToggle) => {
        if (otherToggle !== toggle) {
          otherToggle.nextElementSibling.classList.remove("show")
        }
      })
    })
  })

  // Close dropdowns when clicking outside
  document.addEventListener("click", (event) => {
    if (!event.target.matches(".dropdown-toggle")) {
      const dropdowns = document.querySelectorAll(".dropdown-content")
      dropdowns.forEach((dropdown) => {
        if (dropdown.classList.contains("show") && !dropdown.previousElementSibling.contains(event.target)) {
          dropdown.classList.remove("show")
        }
      })
    }
  })

  // Smooth scrolling for anchor links
  const anchorLinks = document.querySelectorAll('a[href^="#"]:not([href="#"])')
  anchorLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault()
      const targetId = this.getAttribute("href")
      const targetElement = document.querySelector(targetId)

      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop - 80, // Adjust for header height
          behavior: "smooth",
        })

        // Close mobile menu if open
        if (navLinks && navLinks.classList.contains("show")) {
          navLinks.classList.remove("show")
        }
      }
    })
  })
}

// Scroll effects
function initializeScrollEffects() {
  // Back to top button
  const backToTopButton = document.getElementById("backToTop")

  if (backToTopButton) {
    window.addEventListener("scroll", () => {
      if (window.pageYOffset > 300) {
        backToTopButton.style.display = "flex"
      } else {
        backToTopButton.style.display = "none"
      }
    })

    backToTopButton.addEventListener("click", () => {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      })
    })
  }

  // Reveal elements on scroll
  const revealElements = document.querySelectorAll(".reveal")

  if (revealElements.length > 0) {
    function revealOnScroll() {
      const windowHeight = window.innerHeight
      const revealPoint = 150

      revealElements.forEach((element) => {
        const elementTop = element.getBoundingClientRect().top

        if (elementTop < windowHeight - revealPoint) {
          element.classList.add("revealed")
        }
      })
    }

    window.addEventListener("scroll", revealOnScroll)
    revealOnScroll() // Check on page load
  }

  // Sticky header
  const header = document.querySelector("header")
  if (header) {
    const headerOffset = header.offsetTop

    window.addEventListener("scroll", () => {
      if (window.pageYOffset > headerOffset) {
        header.classList.add("sticky")
      } else {
        header.classList.remove("sticky")
      }
    })
  }
}

// FAQ accordion
function initializeFAQ() {
  const faqQuestions = document.querySelectorAll(".faq-question")

  faqQuestions.forEach((question) => {
    question.addEventListener("click", function () {
      const answer = this.nextElementSibling

      // Toggle the current answer
      if (answer.style.display === "block") {
        answer.style.display = "none"
        this.querySelector("span").textContent = "▼"
      } else {
        answer.style.display = "block"
        this.querySelector("span").textContent = "▲"
      }
    })
  })
}

// Plan tabs functionality
function initializePlanTabs() {
  const tabButtons = document.querySelectorAll(".plan-tab-button")
  const tabContents = document.querySelectorAll(".plan-tab-content")

  tabButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const tabId = this.getAttribute("data-tab")

      // Hide all tab contents
      tabContents.forEach((content) => {
        content.style.display = "none"
      })

      // Remove active class from all buttons
      tabButtons.forEach((btn) => {
        btn.classList.remove("active")
      })

      // Show the selected tab content
      document.getElementById(tabId).style.display = "block"

      // Add active class to the clicked button
      this.classList.add("active")
    })
  })

  // Show the first tab by default
  if (tabButtons.length > 0 && tabContents.length > 0) {
    tabButtons[0].click()
  }
}

// Form validation
function validateForm(event) {
  const form = event.target
  const inputs = form.querySelectorAll("input, textarea, select")
  let isValid = true

  inputs.forEach((input) => {
    if (input.hasAttribute("required") && !input.value.trim()) {
      isValid = false
      input.classList.add("error")

      // Create error message if it doesn't exist
      let errorMessage = input.nextElementSibling
      if (!errorMessage || !errorMessage.classList.contains("error-message")) {
        errorMessage = document.createElement("div")
        errorMessage.className = "error-message"
        errorMessage.textContent = "This field is required"
        input.parentNode.insertBefore(errorMessage, input.nextSibling)
      }
    } else {
      input.classList.remove("error")

      // Remove error message if it exists
      const errorMessage = input.nextElementSibling
      if (errorMessage && errorMessage.classList.contains("error-message")) {
        errorMessage.remove()
      }
    }

    // Email validation
    if (input.type === "email" && input.value.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(input.value.trim())) {
        isValid = false
        input.classList.add("error")

        // Create error message if it doesn't exist
        let errorMessage = input.nextElementSibling
        if (!errorMessage || !errorMessage.classList.contains("error-message")) {
          errorMessage = document.createElement("div")
          errorMessage.className = "error-message"
          errorMessage.textContent = "Please enter a valid email address"
          input.parentNode.insertBefore(errorMessage, input.nextSibling)
        }
      }
    }
  })

  if (!isValid) {
    event.preventDefault()
  }
}

// Testimonial slider
function initializeTestimonialSlider() {
  const testimonials = document.querySelectorAll(".testimonial")
  let currentIndex = 0

  function showTestimonial(index) {
    testimonials.forEach((testimonial, i) => {
      testimonial.style.display = i === index ? "block" : "none"
    })
  }

  // Show the first testimonial
  showTestimonial(currentIndex)

  // Create navigation buttons if they don't exist
  const sliderContainer = document.querySelector(".testimonial-slider")

  if (!document.querySelector(".testimonial-nav")) {
    const navContainer = document.createElement("div")
    navContainer.className = "testimonial-nav"

    const prevButton = document.createElement("button")
    prevButton.className = "nav-button prev"
    prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>'

    const nextButton = document.createElement("button")
    nextButton.className = "nav-button next"
    nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>'

    navContainer.appendChild(prevButton)
    navContainer.appendChild(nextButton)
    sliderContainer.appendChild(navContainer)

    // Add event listeners
    prevButton.addEventListener("click", () => {
      currentIndex = (currentIndex - 1 + testimonials.length) % testimonials.length
      showTestimonial(currentIndex)
    })

    nextButton.addEventListener("click", () => {
      currentIndex = (currentIndex + 1) % testimonials.length
      showTestimonial(currentIndex)
    })
  }

  // Auto-rotate testimonials
  setInterval(() => {
    currentIndex = (currentIndex + 1) % testimonials.length
    showTestimonial(currentIndex)
  }, 5000)
}

// Cart functionality
function addToCart(productId, quantity = 1) {
  fetch("/api/add-to-cart/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      product_id: productId,
      quantity: quantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Update cart count
        const cartCount = document.querySelector(".cart-count")
        if (cartCount) {
          cartCount.textContent = data.cart_count
          cartCount.style.display = data.cart_count > 0 ? "flex" : "none"
        }

        // Show success message
        showMessage("Product added to cart successfully!", "success")

        // Update cart modal if open
        if (document.getElementById("cartModal").style.display === "block") {
          fetchCartItems()
        }
      } else {
        showMessage(data.message || "Failed to add product to cart.", "error")
      }
    })
    .catch((error) => {
      console.error("Error adding to cart:", error)
      showMessage("An error occurred. Please try again.", "error")
    })
}

// Fetch cart items for the modal
function fetchCartItems() {
  fetch("/api/get-cart/")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const cartItems = document.getElementById("cartItems")
        const cartTotal = document.getElementById("cartTotal")
        const checkoutBtn = document.getElementById("checkoutBtn")

        cartItems.innerHTML = ""

        if (data.items.length === 0) {
          cartItems.innerHTML = "<p>Your cart is empty.</p>"
          checkoutBtn.style.display = "none"
        } else {
          data.items.forEach((item) => {
            const itemElement = document.createElement("div")
            itemElement.className = "cart-modal-item"
            itemElement.innerHTML = `
                            <div class="item-details">
                                <h4>${item.name}</h4>
                                <p>₹${item.price.toFixed(2)} x ${item.quantity}</p>
                            </div>
                            <p class="item-total">₹${item.total.toFixed(2)}</p>
                        `
            cartItems.appendChild(itemElement)
          })

          cartTotal.textContent = `Total: ₹${data.total.toFixed(2)}`
          checkoutBtn.style.display = "inline-block"
        }
      }
    })
    .catch((error) => {
      console.error("Error fetching cart:", error)
    })
}

// Show message
function showMessage(message, type = "info") {
  const messagesContainer = document.querySelector(".messages")

  if (!messagesContainer) {
    // Create messages container if it doesn't exist
    const container = document.createElement("div")
    container.className = "messages"
    document.body.appendChild(container)
  }

  const messageElement = document.createElement("div")
  messageElement.className = `message ${type}`
  messageElement.innerHTML = `
        <div class="message-content">
            ${message}
            <span class="close-message">&times;</span>
        </div>
    `

  document.querySelector(".messages").appendChild(messageElement)

  // Add event listener to close button
  messageElement.querySelector(".close-message").addEventListener("click", () => {
    messageElement.remove()
  })

  // Auto-hide message after 5 seconds
  setTimeout(() => {
    if (messageElement.parentNode) {
      messageElement.remove()
    }
  }, 5000)
}

// Get CSRF token from cookies
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Quantity input functionality
function initializeQuantityInputs() {
  const quantityContainers = document.querySelectorAll(".quantity-container")

  quantityContainers.forEach((container) => {
    const minusBtn = container.querySelector(".quantity-minus")
    const plusBtn = container.querySelector(".quantity-plus")
    const input = container.querySelector(".quantity-input")

    if (minusBtn && plusBtn && input) {
      minusBtn.addEventListener("click", () => {
        const value = Number.parseInt(input.value)
        if (value > 1) {
          input.value = value - 1
        }
      })

      plusBtn.addEventListener("click", () => {
        const value = Number.parseInt(input.value)
        const max = Number.parseInt(input.getAttribute("max") || 99)
        if (value < max) {
          input.value = value + 1
        }
      })

      input.addEventListener("change", () => {
        const value = Number.parseInt(input.value)
        const min = Number.parseInt(input.getAttribute("min") || 1)
        const max = Number.parseInt(input.getAttribute("max") || 99)

        if (isNaN(value) || value < min) {
          input.value = min
        } else if (value > max) {
          input.value = max
        }
      })
    }
  })
}

// Initialize quantity inputs when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  initializeQuantityInputs()

  // Initialize cart modal
  const cartIcon = document.getElementById("cartIcon")
  const cartModal = document.getElementById("cartModal")
  const closeCart = document.getElementById("closeCart")

  if (cartIcon && cartModal && closeCart) {
    cartIcon.addEventListener("click", () => {
      cartModal.style.display = "block"
      fetchCartItems()
    })

    closeCart.addEventListener("click", () => {
      cartModal.style.display = "none"
    })

    window.addEventListener("click", (event) => {
      if (event.target == cartModal) {
        cartModal.style.display = "none"
      }
    })
  }
})

