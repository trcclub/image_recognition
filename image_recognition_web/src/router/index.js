import Vue from 'vue'
import Router from 'vue-router'
import Manual from 'components/Manual'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Manual',
      component: Manual
    }
  ],
  linkActiveClass: 'is-active'
})
