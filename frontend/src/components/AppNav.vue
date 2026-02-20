<template>
  <div class="header-row header-row-main">
    <div class="header-brand">
      <router-link to="/" class="logo">
        <span class="logo-text">Hockey Screener</span>
      </router-link>
      <nav class="main-nav">
        <router-link
          to="/"
          :class="['nav-btn', { active: $route.path === '/' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18"/>
            <path d="m19 9-5 5-4-4-3 3"/>
          </svg>
          Статистика
        </router-link>
        <router-link
          to="/value-bets"
          :class="['nav-btn', 'nav-btn-value', { active: $route.path === '/value-bets' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          Value Bets
        </router-link>
        <router-link
          to="/lineups"
          :class="['nav-btn', 'nav-btn-lineups', { active: $route.path === '/lineups' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          Составы
        </router-link>
      </nav>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppNav'
}
</script>
