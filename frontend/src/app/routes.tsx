import type { RouteObject } from 'react-router'

import { AppLayout } from '../components/layout/AppLayout'
import { AdminPage } from '../pages/AdminPage'
import { DashboardPage } from '../pages/DashboardPage'
import { GroceryListPage } from '../pages/GroceryListPage'
import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { MealDetailsPage } from '../pages/MealDetailsPage'
import { MealPlanPage } from '../pages/MealPlanPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { ProfilePage } from '../pages/ProfilePage'
import { RegisterPage } from '../pages/RegisterPage'

/** Route table shared by the browser router and the tests. */
export const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'meal-plan', element: <MealPlanPage /> },
      { path: 'meal-plan/meals/:mealId', element: <MealDetailsPage /> },
      { path: 'grocery-list', element: <GroceryListPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'admin', element: <AdminPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
