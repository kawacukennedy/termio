

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/0.Cxqyw10L.js","_app/immutable/chunks/myKowI8s.js","_app/immutable/chunks/CK5bAZH2.js"];
export const stylesheets = [];
export const fonts = [];
