// Корневой компонент: шапка с навигацией и маршрутизация между страницами
// загрузки и поиска.

import { NavLink, Route, Routes } from "react-router-dom";

import { HomePage } from "./pages/HomePage";
import { SearchPage } from "./pages/SearchPage";

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <div className="app__brand">
          <span className="app__logo">🔎</span>
          <span>База знаний университета</span>
        </div>
        <nav className="app__nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `app__navlink${isActive ? " app__navlink--active" : ""}`
            }
          >
            Загрузка
          </NavLink>
          <NavLink
            to="/search"
            className={({ isActive }) =>
              `app__navlink${isActive ? " app__navlink--active" : ""}`
            }
          >
            Поиск
          </NavLink>
        </nav>
      </header>

      <main className="app__main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </main>

      <footer className="app__footer">
        Интеллектуальная поисковая система · учебная практика БПИ24
      </footer>
    </div>
  );
}
