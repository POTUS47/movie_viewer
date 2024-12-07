import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import TestView from '@/views/TestView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/about',
    name: 'about',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
  },
  {
    path: '/test',
    name: 'test',
    component: TestView,
  },
  {
    path: '/search-by-title',
    component:()=>import('../views/SearchByTitle.vue')
  },
  {
    path: '/search-by-actor',
    component: () => import('../views/SearchByActor.vue')
  },
  {
    path: '/search-by-director',
    component: () => import('../views/SearchByDirector.vue')
  },
  {
    path: '/search-by-time',
    component: () => import('../views/SearchByTime.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
