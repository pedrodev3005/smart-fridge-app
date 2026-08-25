function Home({ produtos }) {

  return (
    <main className="content">
      <section className="card destaque">
        <span>Minha geladeira</span>
        <h2>{produtos.length} produtos</h2>
        <p>Inventário atualizado automaticamente</p>
      </section>

      <section className="card">
        <h2>Produtos disponíveis</h2>

        <div className="product-list">
          {produtos.map((produto) => (
            <div className="product" key={produto.id}>
              <div className="product-icon">✓</div>
              <span>{produto.nome}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>Último evento</h2>

        <div className="event">
          <div className="event-icon">+</div>

          <div>
            <strong>Leite adicionado</strong>
            <p>Hoje, 14:32</p>
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Receitas para você</h2>
        <p>
          Descubra receitas que podem ser preparadas com os produtos
          disponíveis na sua geladeira.
        </p>
      </section>


      <section className="card">
        <h2>Produto pendente</h2>

        <p>
            Um novo produto precisa ser identificado.
        </p>

        <a
            className="primary-button notification-link"
            href="/produto-desconhecido"
        >
            Identificar produto
        </a>
     </section>  
    </main>
  )
}

export default Home