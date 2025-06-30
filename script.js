document.addEventListener('DOMContentLoaded', function() {
    const scrollButton = document.createElement('button');
    scrollButton.innerText = 'Back to Top';
    scrollButton.classList.add('scroll-top');
    document.body.appendChild(scrollButton);
  
    scrollButton.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  
    const style = document.createElement('style');
    style.innerHTML = `
      .scroll-top {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1.2em;
      }
      .scroll-top:hover {
        background-color: #45a049;
      }
    `;
    document.head.appendChild(style);
  });

document.querySelector('.mobile-menu').addEventListener('click', function() {
    document.querySelector('nav ul').classList.toggle('show');
});

document.querySelectorAll('nav a').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        if(targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if(targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 70,
                behavior: 'smooth'
            });
            
            document.querySelector('nav ul').classList.remove('show');
        }
    });
});

window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    if(window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});


const testimonials = document.querySelectorAll('.testimonial');
const prevBtn = document.querySelector('.prev');
const nextBtn = document.querySelector('.next');
let currentIndex = 0;

function showTestimonial(index) {
    testimonials.forEach(testimonial => {
        testimonial.classList.remove('active');
    });
    
    testimonials[index].classList.add('active');
}

prevBtn.addEventListener('click', function() {
    currentIndex = (currentIndex - 1 + testimonials.length) % testimonials.length;
    showTestimonial(currentIndex);
});

nextBtn.addEventListener('click', function() {
    currentIndex = (currentIndex + 1) % testimonials.length;
    showTestimonial(currentIndex);
});

let testimonialInterval = setInterval(() => {
    currentIndex = (currentIndex + 1) % testimonials.length;
    showTestimonial(currentIndex);
}, 5000);

document.querySelector('.testimonial-slider').addEventListener('mouseenter', function() {
    clearInterval(testimonialInterval);
});

document.querySelector('.testimonial-slider').addEventListener('mouseleave', function() {
    testimonialInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % testimonials.length;
        showTestimonial(currentIndex);
    }, 5000);
});


document.getElementById('enquiryForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        service: document.getElementById('service').value,
        message: document.getElementById('message').value
    };
    
    try {
        const response = await fetch('/submit-enquiry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if(response.ok) {
            alert('Thank you for your enquiry! We will contact you shortly.');
            this.reset();
        } else {
            throw new Error('Failed to submit enquiry');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('There was an error submitting your enquiry. Please try again.');
    }
});

document.getElementById('newsletterForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = this.querySelector('input').value;
    
    try {
        const response = await fetch('/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });
        
        if(response.ok) {
            alert('Thank you for subscribing to our newsletter!');
            this.reset();
        } else {
            throw new Error('Failed to subscribe');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('There was an error subscribing. Please try again.');
    }
});

showTestimonial(0);