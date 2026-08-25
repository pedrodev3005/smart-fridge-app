import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
} from 'react-router-dom'

import { useState } from 'react'

import Home from './pages/Home'
import Inventory from './pages/Inventory'
import Recipes from './pages/Recipes'
import System from './pages/System'
import UnknownProduct from './pages/UnknownProduct'

import './App.css'

function App() {
  const [produtos, setProdutos] = useState([
    {
      id: 1,
      nome: 'Leite',
      categoria: 'Laticínios',
      status: 'Disponível',
    },
    {
      id: 2,
      nome: 'Ovos',
      categoria: 'Proteínas',
      status: 'Disponível',
    },
    {
      id: 3,
      nome: 'Queijo',
      categoria: 'Laticínios',
      status: 'Disponível',
    },
    {
      id: 4,
      nome: 'Tomate',
      categoria: 'Hortaliças',
      status: 'Disponível',
    },
    {
      id: 5,
      nome: 'Iogurte',
      categoria: 'Laticínios',
      status: 'Disponível',
    },
  ])

  function adicionarProduto(novoProduto) {
    const produto = {
      id: Date.now(),
      nome: novoProduto.nome,
      categoria: novoProduto.categoria,
      status: 'Disponível',
    }

    setProdutos([...produtos, produto])
  }

  return (
    <BrowserRouter>
      <div className="app">
        <header className="header">
          <h1>Smart Fridge</h1>
          <p>Sua geladeira inteligente</p>
        </header>

        <Routes>
          <Route
            path="/"
            element={<Home produtos={produtos} />}
          />

          <Route
            path="/inventario"
            element={<Inventory produtos={produtos} />}
          />

          <Route
            path="/receitas"
            element={<Recipes />}
          />

          <Route
            path="/sistema"
            element={<System />}
          />

          <Route
            path="/produto-desconhecido"
            element={
              <UnknownProduct
                adicionarProduto={adicionarProduto}
              />
            }
          />
        </Routes>

        <nav className="bottom-nav">
          <NavLink to="/">Início</NavLink>
          <NavLink to="/inventario">Inventário</NavLink>
          <NavLink to="/receitas">Receitas</NavLink>
          <NavLink to="/sistema">Sistema</NavLink>
        </nav>
      </div>
    </BrowserRouter>
  )
}

export default App