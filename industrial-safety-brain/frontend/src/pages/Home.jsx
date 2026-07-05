import ChatBox from "../components/ChatBox";

function Home() {
  return (
    <main className="home">
      <header className="home__header">
        <div className="home__logo">🛡️</div>
        <h1 className="home__title">Industrial Safety Brain</h1>
        <p className="home__subtitle">AI-Powered Safety Intelligence</p>
      </header>
      <ChatBox />
    </main>
  );
}

export default Home;
