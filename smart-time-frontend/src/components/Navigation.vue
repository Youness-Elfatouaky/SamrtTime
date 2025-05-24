<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import {
  UserIcon,
  HomeIcon,
  ClipboardDocumentListIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Tasks', href: '/tasks', icon: ClipboardDocumentListIcon },
  { name: 'Meetings', href: '/meetings', icon: CalendarIcon },
  { name: 'Chat', href: '/chat', icon: ChatBubbleLeftRightIcon },
]

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<template>
  <nav class="bg-white shadow">
    <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="relative flex justify-between h-16">
        <div class="flex-1 flex items-center justify-between">
          <!-- Logo and Brand -->
          <div class="flex-shrink-0 flex items-center">
            <router-link to="/dashboard" class="flex items-center space-x-2">
              <CalendarIcon class="h-8 w-8 text-blue-600" />
              <span class="text-xl font-bold text-blue-600">SmartTime</span>
            </router-link>
          </div>

          <!-- Desktop Navigation -->
          <div class="hidden lg:flex lg:items-center lg:space-x-6">
            <router-link
              v-for="item in navigation"
              :key="item.name"
              :to="item.href"
              class="flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150"
              :class="[$route.path === item.href 
                ? 'bg-blue-50 text-blue-700' 
                : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50']"
            >
              <component :is="item.icon" class="h-5 w-5 mr-2" />
              {{ item.name }}
            </router-link>
          </div>

          <!-- User Menu -->
          <div class="flex items-center space-x-4">
            <span class="hidden lg:block text-sm text-gray-600">
              {{ new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}
            </span>
            <Menu as="div" class="relative">
              <MenuButton class="flex items-center space-x-2 bg-white rounded-full p-1 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <UserIcon class="h-8 w-8 text-gray-600 p-1" />
                <span class="hidden lg:block text-sm font-medium text-gray-700">Account</span>
              </MenuButton>

              <transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <MenuItems class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                  <MenuItem>
                    <button
                      @click="logout"
                      class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                    >
                      <span class="mr-2">🚪</span>
                      Sign out
                    </button>
                  </MenuItem>
                </MenuItems>
              </transition>
            </Menu>
          </div>
        </div>

        <!-- Mobile Navigation -->
        <div class="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
          <div class="flex justify-around">
            <router-link
              v-for="item in navigation"
              :key="item.name"
              :to="item.href"
              class="flex flex-col items-center py-2 px-3"
              :class="[$route.path === item.href 
                ? 'text-blue-600' 
                : 'text-gray-600 hover:text-blue-600']"
            >
              <component :is="item.icon" class="h-6 w-6" />
              <span class="text-xs mt-1">{{ item.name }}</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
