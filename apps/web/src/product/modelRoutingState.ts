type PluginBinding = { capability: string; model_profile_id: string; registry_key?: string | null; registry_version?: string };
type Profiles = Record<string, { capability_bindings: Record<string, { adapter_key: string; adapter_version: string } | undefined> }>;

export function retargetPlugin<T extends PluginBinding>(plugin: T, targetId: string, profiles: Profiles) {
  const binding = profiles[targetId]?.capability_bindings[plugin.capability];
  return { ...plugin, model_profile_id: targetId, registry_key: binding?.adapter_key ?? null, registry_version: binding?.adapter_version ?? "1" };
}
