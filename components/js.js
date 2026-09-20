class NavigationEffect {
  constructor(navigation) {
    this.previous = null;
    this.current = null;
    this.navigation = navigation;
    this.anchors = this.navigation.querySelectorAll("a");
    this.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890*#@/*!%&^";

    this.initEvents();
  }

  initEvents() {
    this.anchors.forEach((anchor) => {
      const cachedText = anchor.querySelector("span").innerText;

      anchor.addEventListener("mouseenter", () => {
        this.handleHover(anchor, cachedText);
      });

      anchor.addEventListener("click", (e) => {
        e.preventDefault(); 
        this.handlePrevious();
        this.handleCurrent(anchor);
      });
    });
  }

  handleHover(element, cachedText) {
    const span = element.querySelector("span");
    let iteration = 0;
    
    clearInterval(span.dataset.interval);

    span.dataset.interval = setInterval(() => {
      span.innerText = cachedText
        .split("")
        .map((letter, index) => {
          if (index < iteration) return cachedText[index];
          return this.chars[Math.floor(Math.random() * this.chars.length)];
        })
        .join("");

      if (iteration >= cachedText.length) {
        clearInterval(span.dataset.interval);
      }
      iteration += 1 / 3;
    }, 30);
  }

  handleCurrent(current) {
    this.current = current;
    this.current.classList.add("active");
    const nodes = this.getNodes(this.current);

    gsap.to(nodes[0], {
      duration: 0.9,
      ease: "rough({strength: 5, points: 50})",
      attr: { x: "0%" },
      overwrite: true,
      stagger: 0.012
    });

    gsap.to(nodes[1], {
      duration: 0.9,
      ease: "rough({strength: 5, points: 50})",
      attr: { x: "0%" },
      stagger: 0.012,
      overwrite: true,
      delay: 0.1
    });

    gsap.fromTo(
      [nodes[1], nodes[0]],
      { opacity: 1 },
      {
        opacity: 0.75,
        duration: 0.13,
        ease: "rough({strength: 5, points: 50})",
        repeat: -1,
        delay: 1.1
      }
    );
  }

  handlePrevious() {
    this.previous = this.navigation.querySelector("a.active");
    if (this.previous) {
      this.previous.classList.remove("active");
      const nodes = this.getNodes(this.previous);
      
      gsap.to(nodes[0], {
        duration: 0.2,
        ease: "power1.out",
        attr: { x: "-101%" },
        overwrite: true
      });

      gsap.to(nodes[1], {
        duration: 0.2,
        ease: "power1.out",
        attr: { x: "-101%" },
        overwrite: true,
        delay: 0.02
      });
    }
  }

  getNodes(item) {
    return [
      gsap.utils.shuffle(gsap.utils.selector(item)(".blue rect")),
      gsap.utils.shuffle(gsap.utils.selector(item)(".pink rect"))
    ];
  }
}

// Bloque descomentado para inicializar la animación y el menú
document.addEventListener("DOMContentLoaded", () => {
  // Registrar solo los plugins necesarios
  gsap.registerPlugin(EasePack);

  const navElement = document.querySelector("#main-nav");
  new NavigationEffect(navElement);

  // ANIMACIÓN DE DESPLIEGUE HORIZONTAL 
  // (Aparece al cargar la página sin errores)
  const tl = gsap.timeline({ delay: 0.5 });

  tl.to(navElement, {
    duration: 1.2,
    clipPath: "inset(0% 0% 0% 0%)",
    opacity: 1,
    ease: "power3.inOut"
  }).from(
    navElement.querySelectorAll("a"),
    {
      duration: 0.6,
      y: 15,
      opacity: 0,
      stagger: 0.08,
      ease: "power2.out"
    },
    "-=0.6" 
  );
});

