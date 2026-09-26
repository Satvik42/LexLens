import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../state/authStore';
import { Button, IconButton } from '../ui';
import Logo from './Logo';
import './layout.css';

const LANDING_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/#how-it-works', label: 'How it works', hash: true },
  { to: '/#features', label: 'Features', hash: true },
  { to: '/#faq', label: 'FAQ', hash: true },
];

const APP_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/documents', label: 'My Documents' },
];

/** Restrained top navigation (design_plan §8). Landing shows marketing links; the app shows Home / My Documents. */
export default function Navbar({ variant = 'app', embedded = false }) {
  const { status, session, signOut } = useAuthStore();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const links = variant === 'landing' ? LANDING_LINKS : APP_LINKS;
  const initial = session?.email?.[0]?.toUpperCase() ?? 'U';

  async function handleSignOut() {
    await signOut();
    navigate('/');
  }

  return (
    <header className={`navbar ${embedded ? 'navbar--embedded' : ''}`}>
      <div className="container navbar__inner">
        <Link to="/" className="navbar__brand" aria-label="LexLens home">
          <Logo />
        </Link>
        <nav className={`navbar__nav ${open ? 'is-open' : ''}`} aria-label="Primary">
          <ul className="navbar__links" onClick={() => setOpen(false)}>
            {links.map((link) => (
              <li key={link.to}>
                {link.hash ? (
                  <a href={link.to} className="navbar__link">
                    {link.label}
                  </a>
                ) : (
                  <NavLink to={link.to} end={link.end} className={({ isActive }) => `navbar__link ${isActive ? 'navbar__link--active' : ''}`}>
                    {link.label}
                  </NavLink>
                )}
              </li>
            ))}
          </ul>
        </nav>
        <div className="navbar__actions">
          {status === 'signed_in' ? (
            <div className="navbar__user">
              <span className="navbar__avatar" aria-hidden="true">
                {initial}
              </span>
              <span className="sr-only">Signed in as {session.email}</span>
              <Button variant="ghost" size="sm" icon="logout" onClick={handleSignOut}>
                Sign out
              </Button>
            </div>
          ) : (
            <>
              <Button variant="secondary" size="sm" to="/signin">
                Sign in
              </Button>
              <Button size="sm" to="/upload">
                Get started
              </Button>
            </>
          )}
          <IconButton
            className="navbar__menu"
            icon="menu"
            label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((value) => !value)}
          />
        </div>
      </div>
    </header>
  );
}
