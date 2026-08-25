import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function UnknownProduct({ adicionarProduto }) {
  const [nome, setNome] = useState('')
  const [categoria, setCategoria] = useState('')

  const navigate = useNavigate()

  function handleSubmit(event) {
    event.preventDefault()

    if (!nome || !categoria) {
      alert('Preencha o nome e a categoria do produto.')
      return
    }

    adicionarProduto({
      nome,
      categoria,
    })

    navigate('/inventario')
  }

  return (
    <main className="content">
      <section className="card unknown-card">
        <div className="unknown-alert">
          !
        </div>

        <div>
          <h2>Novo produto detectado</h2>
          <p>
            O sistema detectou um novo produto na geladeira,
            mas não conseguiu identificá-lo automaticamente.
          </p>
        </div>
      </section>

      <section className="card">
        <div className="unknown-image">
          Imagem do produto
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="product-name">
              Nome do produto
            </label>

            <input
              id="product-name"
              type="text"
              placeholder="Ex.: Suco de uva"
              value={nome}
              onChange={(event) => setNome(event.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="category">
              Categoria
            </label>

            <select
              id="category"
              value={categoria}
              onChange={(event) => setCategoria(event.target.value)}
            >
              <option value="">
                Selecione uma categoria
              </option>

              <option value="Laticínios">
                Laticínios
              </option>

              <option value="Bebidas">
                Bebidas
              </option>

              <option value="Frutas">
                Frutas
              </option>

              <option value="Hortaliças">
                Hortaliças
              </option>

              <option value="Proteínas">
                Proteínas
              </option>

              <option value="Outros">
                Outros
              </option>
            </select>
          </div>

          <button
            className="primary-button full-button"
            type="submit"
          >
            Adicionar ao inventário
          </button>
        </form>
      </section>
    </main>
  )
}

export default UnknownProduct