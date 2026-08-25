function Recipes() {
  return (
    <main className="content">
      <section className="card">
        <h2>Receitas</h2>

        <p>
          Aqui serão exibidas receitas sugeridas com base nos produtos
          disponíveis na geladeira.
        </p>
      </section>

      <section className="card">
        <h3>Omelete de queijo e tomate</h3>
        <p>Ingredientes disponíveis: 3/3</p>
        <p>Calorias estimadas: 320 kcal</p>
      </section>

      <section className="card">
        <h3>Panqueca</h3>
        <p>Ingredientes disponíveis: 3/4</p>
        <p>Falta: farinha de trigo</p>
      </section>
    </main>
  )
}

export default Recipes