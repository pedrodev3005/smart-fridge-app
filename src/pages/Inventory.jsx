function Inventory({ produtos }) {
  return (
    <main className="content">
      <section className="card">
        <div className="card-title">
          <div>
            <h2>Inventário</h2>
            <p>
              Produtos atualmente disponíveis na geladeira.
            </p>
          </div>

          <span className="inventory-count">
            {produtos.length} itens
          </span>
        </div>

        <div className="inventory-list">
          {produtos.map((produto) => (
            <div className="inventory-item" key={produto.id}>
              <div className="inventory-info">
                <strong>{produto.nome}</strong>
                <span>{produto.categoria}</span>
              </div>

              <span className="status">
                {produto.status}
              </span>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

export default Inventory