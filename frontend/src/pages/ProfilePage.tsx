import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { SelectField, TextField } from '../components/ui/FormField'
import {
  ACTIVITY_LEVELS,
  ALLERGENS,
  DIETARY_PREFERENCES,
  GENDERS,
  HEALTH_GOALS,
} from '../features/profile/options'

export function ProfilePage() {
  return (
    <>
      <PageHeader
        eyebrow="Profile"
        title="Set up your nutrition profile"
        description="These details are turned into your nutrition target (BMI, daily calories and protein) before any meals are recommended."
      />
      <div className="space-y-6">
        <DevelopmentNotice milestone="auth">
          Saving and editing profiles (REQ-4.1.3 – REQ-4.1.5) arrives with authentication. The form
          below shows the fields that will be captured and is disabled for now.
        </DevelopmentNotice>

        <form aria-label="Profile form" onSubmit={(e) => e.preventDefault()}>
          <fieldset disabled className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <div className="space-y-6">
              <Card>
                <CardTitle>About you</CardTitle>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <TextField label="Age" type="number" inputMode="numeric" />
                  <SelectField label="Gender" options={GENDERS} />
                  <TextField label="Height (cm)" type="number" inputMode="decimal" />
                  <TextField label="Weight (kg)" type="number" inputMode="decimal" />
                  <SelectField label="Activity level" options={ACTIVITY_LEVELS} />
                </div>
              </Card>

              <Card>
                <CardTitle>Diet and allergies</CardTitle>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <SelectField label="Dietary preference" options={DIETARY_PREFERENCES} />
                </div>
                <p className="mt-4 text-sm font-medium text-ink">Declared allergies</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {ALLERGENS.map((allergen) => (
                    <label
                      key={allergen}
                      className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-ink"
                    >
                      <input type="checkbox" className="accent-brand-600" />
                      {allergen}
                    </label>
                  ))}
                </div>
              </Card>

              <Card>
                <CardTitle>Goals and constraints</CardTitle>
                <div className="mt-4 grid gap-4 sm:grid-cols-3">
                  <SelectField label="Health goal" options={HEALTH_GOALS} />
                  <TextField label="Weekly budget (₹)" type="number" inputMode="decimal" />
                  <TextField label="Cooking time per meal (min)" type="number" inputMode="numeric" />
                </div>
              </Card>

              <Button type="submit">Save profile</Button>
            </div>

            <Card className="h-fit">
              <CardTitle>Your nutrition profile</CardTitle>
              <CardDescription>
                Once your profile is saved, this panel will show your BMI, activity-adjusted
                calorie target and protein target.
              </CardDescription>
            </Card>
          </fieldset>
        </form>
      </div>
    </>
  )
}
