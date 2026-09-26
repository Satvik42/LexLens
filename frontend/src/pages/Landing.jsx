import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Icon } from '../components/ui';
import Navbar from '../components/layout/Navbar';
import HeroVisual from '../components/landing/HeroVisual';

const BULLETS = [
  'Find key terms in seconds',
  'See the exact source in your document',
  'Identify risks and inconsistencies',
  'Prepare questions for a legal professional',
];

function UploadScene() {
  return (
    <div className="scene scene--upload" aria-hidden="true">
      <span className="scene-file scene-file--pdf">PDF</span>
      <span className="scene-file scene-file--doc">DOCX</span>
      <span className="scene-file scene-file--txt">TXT</span>
    </div>
  );
}

function ChooseScene() {
  return (
    <div className="scene scene--choose" aria-hidden="true">
      <span className="scene-tile scene-tile--green">Notice</span>
      <span className="scene-tile scene-tile--amber">Pay</span>
      <span className="scene-tile scene-tile--rose">Risks</span>
      <span className="scene-tile scene-tile--blue">Duties</span>
    </div>
  );
}

function EvidenceScene() {
  return (
    <div className="scene scene--evidence" aria-hidden="true">
      <span className="scene-line" />
      <span className="scene-line scene-line--mark">60 days</span>
      <span className="scene-line scene-line--short" />
      <span className="scene-chip">Page 8 · §8.2</span>
    </div>
  );
}

function MissingScene() {
  return (
    <div className="scene scene--missing" aria-hidden="true">
      <span className="scene-empty">Not in this document</span>
      <span className="scene-ask">Ask a lawyer</span>
    </div>
  );
}

function OperationsScene() {
  return (
    <div className="scene scene--ops" aria-hidden="true">
      <span>Terms</span>
      <span>Pay</span>
      <span>Notice</span>
      <span>Risks</span>
    </div>
  );
}

function SourceScene() {
  return (
    <div className="scene scene--source" aria-hidden="true">
      <strong>60 days</strong>
      <em>Page 8 · §8.2</em>
    </div>
  );
}

function ConflictScene() {
  return (
    <div className="scene scene--conflict" aria-hidden="true">
      <span>30 days</span>
      <span>60 days</span>
    </div>
  );
}

function PrepScene() {
  return (
    <ol className="scene scene--prep" aria-hidden="true">
      <li>What if I resign?</li>
      <li>Which notice applies?</li>
      <li>Is equity covered?</li>
    </ol>
  );
}

const STEPS = [
  { title: 'Upload a document', Scene: UploadScene },
  { title: 'Choose what to understand', Scene: ChooseScene },
  { title: 'Read the evidence', Scene: EvidenceScene },
  { title: 'Know what is missing', Scene: MissingScene },
];

const FEATURES = [
  { title: 'One screen per question', Scene: OperationsScene },
  { title: 'The clause, not a score', Scene: SourceScene },
  { title: 'Both sides, side by side', Scene: ConflictScene },
  { title: 'Questions for a lawyer', Scene: PrepScene },
];

const FAQ = [
  {
    q: 'Is LexLens a lawyer or legal advice?',
    a: 'No. LexLens provides document-grounded information and assistance. It is not a substitute for professional legal advice.',
  },
  {
    q: 'What happens if something is not in the document?',
    a: 'We say it cannot be determined, show what we looked for, and suggest questions for a legal professional. We do not invent an answer.',
  },
  {
    q: 'Which documents can I upload?',
    a: 'Employment, rental, NDA, freelance, vendor, internship, SaaS, founder, partnership, service and general agreements — the same operations adapt to the type.',
  },
  {
    q: 'Where do the answers come from?',
    a: 'From clauses retrieved in your uploaded document. Quotes are checked against the parsed pages before they are shown as verified.',
  },
];

function Reveal({ id, children }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true);
      return undefined;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -6% 0px' },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <section id={id} ref={ref} className={`landing-section reveal ${visible ? 'is-visible' : ''}`}>
      {children}
    </section>
  );
}

export default function Landing() {
  const [step, setStep] = useState(0);
  const [openFaq, setOpenFaq] = useState(0);

  return (
    <>
      <section className="landing-frame">
        <Navbar variant="landing" embedded />
        <div className="hero__grid">
          <div className="hero__copy">
            <h1 className="hero__title">
              Understand what you&apos;re <span className="hero__accent">signing.</span>
            </h1>
            <p className="hero__lede">
              AI-powered legal document analysis that shows you what matters, where it appears, and what you should
              verify.
            </p>
            <ul className="hero__bullets">
              {BULLETS.map((item) => (
                <li key={item}>
                  <Icon name="checkCircle" size={18} />
                  {item}
                </li>
              ))}
            </ul>
            <div className="hero__cta">
              <Button to="/upload" iconRight="arrowRight" size="lg">
                Analyze a Document
              </Button>
              <a className="hero__link" href="#how-it-works">
                See how it works
              </a>
            </div>
          </div>
          <HeroVisual />
        </div>
        <footer className="hero__trust">
          <p>Secure &amp; private · Evidence-backed answers</p>
          <p>Not a substitute for professional legal advice.</p>
        </footer>
      </section>

      <Reveal id="how-it-works">
        <header className="reveal-item landing-section__head">
          <p className="eyebrow">How it works</p>
          <h2 className="page-title">See where it came from.</h2>
        </header>
        <ol className="step-grid">
          {STEPS.map((item, index) => (
            <li key={item.title} className={`reveal-item step-card ${index === step ? 'is-active' : ''}`}>
              <button type="button" className="step-card__button" aria-pressed={index === step} onClick={() => setStep(index)}>
                <item.Scene />
                <span className="step-num">{String(index + 1).padStart(2, '0')}</span>
                <h3>{item.title}</h3>
              </button>
            </li>
          ))}
        </ol>
      </Reveal>

      <Reveal id="features">
        <header className="reveal-item landing-section__head">
          <p className="eyebrow">Features</p>
          <h2 className="page-title">A companion, not a chatbot.</h2>
        </header>
        <div className="feature-grid">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="reveal-item feature-item">
              <feature.Scene />
              <h3>{feature.title}</h3>
            </article>
          ))}
        </div>
      </Reveal>

      <Reveal id="faq">
        <header className="reveal-item landing-section__head">
          <p className="eyebrow">FAQ</p>
          <h2 className="page-title">Questions people ask first</h2>
        </header>
        <div className="faq">
          {FAQ.map((item, index) => {
            const open = openFaq === index;
            return (
              <div key={item.q} className={`reveal-item faq__item ${open ? 'is-open' : ''}`}>
                <h3>
                  <button
                    type="button"
                    className="faq__button"
                    aria-expanded={open}
                    onClick={() => setOpenFaq(open ? -1 : index)}
                  >
                    {item.q}
                    <Icon name={open ? 'chevronLeft' : 'chevronRight'} size={16} />
                  </button>
                </h3>
                {open ? <p className="text-secondary faq__answer">{item.a}</p> : null}
              </div>
            );
          })}
        </div>
        <div className="reveal-item landing-end">
          <Button to="/upload" iconRight="arrowRight" size="lg">
            Analyze a Document
          </Button>
          <p className="text-secondary text-sm">
            Or <Link to="/signin">sign in</Link> to see documents you have already uploaded.
          </p>
        </div>
      </Reveal>
    </>
  );
}
