import { c as create_ssr_component, b as compute_rest_props, d as spread, f as escape_object, h as escape_attribute_value, i as each, v as validate_component, a as subscribe, j as createEventDispatcher, k as add_attribute, e as escape } from "../../chunks/ssr.js";
import { d as derived, w as writable } from "../../chunks/index.js";
const void_element_names = /^(?:area|base|br|col|command|embed|hr|img|input|keygen|link|meta|param|source|track|wbr)$/;
function is_void(name) {
  return void_element_names.test(name) || name.toLowerCase() === "!doctype";
}
const defaultState = {
  conversations: [],
  currentConversationId: null,
  notifications: [],
  syncState: {
    status: "idle",
    lastSync: null,
    pendingChanges: 0
  },
  plugins: [],
  serverUrl: "http://localhost:8080",
  isLoading: false
};
function createAppStore() {
  const { subscribe: subscribe2, set, update } = writable(defaultState);
  return {
    subscribe: subscribe2,
    set,
    update,
    setServerUrl: (url) => update((s) => ({ ...s, serverUrl: url })),
    setLoading: (loading) => update((s) => ({ ...s, isLoading: loading })),
    addConversation: (conversation) => update((s) => ({ ...s, conversations: [conversation, ...s.conversations] })),
    setCurrentConversation: (id) => update((s) => ({ ...s, currentConversationId: id })),
    addMessage: (conversationId, message) => update((s) => ({
      ...s,
      conversations: s.conversations.map(
        (c) => c.id === conversationId ? { ...c, messages: [...c.messages, message], updatedAt: (/* @__PURE__ */ new Date()).toISOString() } : c
      )
    })),
    setNotifications: (notifications) => update((s) => ({ ...s, notifications })),
    markNotificationRead: (id) => update((s) => ({
      ...s,
      notifications: s.notifications.map(
        (n) => n.id === id ? { ...n, read: true } : n
      )
    })),
    setSyncState: (syncState) => update((s) => ({ ...s, syncState })),
    setPlugins: (plugins) => update((s) => ({ ...s, plugins })),
    togglePlugin: (id) => update((s) => ({
      ...s,
      plugins: s.plugins.map(
        (p) => p.id === id ? { ...p, enabled: !p.enabled } : p
      )
    })),
    reset: () => set(defaultState)
  };
}
const appStore = createAppStore();
const currentConversation = derived(
  appStore,
  ($store) => $store.conversations.find((c) => c.id === $store.currentConversationId) || null
);
const unreadNotifications = derived(
  appStore,
  ($store) => $store.notifications.filter((n) => !n.read).length
);
/**
 * @license lucide-svelte v0.300.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const defaultAttributes = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": 2,
  "stroke-linecap": "round",
  "stroke-linejoin": "round"
};
const Icon = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["name", "color", "size", "strokeWidth", "absoluteStrokeWidth", "iconNode"]);
  let { name } = $$props;
  let { color = "currentColor" } = $$props;
  let { size = 24 } = $$props;
  let { strokeWidth = 2 } = $$props;
  let { absoluteStrokeWidth = false } = $$props;
  let { iconNode } = $$props;
  if ($$props.name === void 0 && $$bindings.name && name !== void 0) $$bindings.name(name);
  if ($$props.color === void 0 && $$bindings.color && color !== void 0) $$bindings.color(color);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0) $$bindings.size(size);
  if ($$props.strokeWidth === void 0 && $$bindings.strokeWidth && strokeWidth !== void 0) $$bindings.strokeWidth(strokeWidth);
  if ($$props.absoluteStrokeWidth === void 0 && $$bindings.absoluteStrokeWidth && absoluteStrokeWidth !== void 0) $$bindings.absoluteStrokeWidth(absoluteStrokeWidth);
  if ($$props.iconNode === void 0 && $$bindings.iconNode && iconNode !== void 0) $$bindings.iconNode(iconNode);
  return `<svg${spread(
    [
      escape_object(defaultAttributes),
      escape_object($$restProps),
      { width: escape_attribute_value(size) },
      { height: escape_attribute_value(size) },
      { stroke: escape_attribute_value(color) },
      {
        "stroke-width": escape_attribute_value(absoluteStrokeWidth ? Number(strokeWidth) * 24 / Number(size) : strokeWidth)
      },
      {
        class: escape_attribute_value(`lucide-icon lucide lucide-${name} ${$$props.class ?? ""}`)
      }
    ],
    {}
  )}>${each(iconNode, ([tag, attrs]) => {
    return `${((tag$1) => {
      return tag$1 ? `<${tag}${spread([escape_object(attrs)], {})}>${is_void(tag$1) ? "" : ``}${is_void(tag$1) ? "" : `</${tag$1}>`}` : "";
    })(tag)}`;
  })}${slots.default ? slots.default({}) : ``}</svg>`;
});
const Bell = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"
      }
    ],
    ["path", { "d": "M10.3 21a1.94 1.94 0 0 0 3.4 0" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bell" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Bot = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M12 8V4H8" }],
    [
      "rect",
      {
        "width": "16",
        "height": "12",
        "x": "4",
        "y": "8",
        "rx": "2"
      }
    ],
    ["path", { "d": "M2 14h2" }],
    ["path", { "d": "M20 14h2" }],
    ["path", { "d": "M15 13v2" }],
    ["path", { "d": "M9 13v2" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bot" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Cloud_off = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "m2 2 20 20" }],
    [
      "path",
      {
        "d": "M5.782 5.782A7 7 0 0 0 9 19h8.5a4.5 4.5 0 0 0 1.307-.193"
      }
    ],
    [
      "path",
      {
        "d": "M21.532 16.5A4.5 4.5 0 0 0 17.5 10h-1.79A7.008 7.008 0 0 0 10 5.07"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "cloud-off" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Cloud = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "cloud" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Copy = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "14",
        "height": "14",
        "x": "8",
        "y": "8",
        "rx": "2",
        "ry": "2"
      }
    ],
    [
      "path",
      {
        "d": "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "copy" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Hard_drive = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "line",
      {
        "x1": "22",
        "x2": "2",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "path",
      {
        "d": "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
      }
    ],
    [
      "line",
      {
        "x1": "6",
        "x2": "6.01",
        "y1": "16",
        "y2": "16"
      }
    ],
    [
      "line",
      {
        "x1": "10",
        "x2": "10.01",
        "y1": "16",
        "y2": "16"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "hard-drive" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Message_square = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "message-square" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Mic = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"
      }
    ],
    ["path", { "d": "M19 10v2a7 7 0 0 1-14 0v-2" }],
    [
      "line",
      {
        "x1": "12",
        "x2": "12",
        "y1": "19",
        "y2": "22"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "mic" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Paperclip = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "paperclip" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Plus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M5 12h14" }], ["path", { "d": "M12 5v14" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "plus" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Puzzle = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M19.439 7.85c-.049.322.059.648.289.878l1.568 1.568c.47.47.706 1.087.706 1.704s-.235 1.233-.706 1.704l-1.611 1.611a.98.98 0 0 1-.837.276c-.47-.07-.802-.48-.968-.925a2.501 2.501 0 1 0-3.214 3.214c.446.166.855.497.925.968a.979.979 0 0 1-.276.837l-1.61 1.61a2.404 2.404 0 0 1-1.705.707 2.402 2.402 0 0 1-1.704-.706l-1.568-1.568a1.026 1.026 0 0 0-.877-.29c-.493.074-.84.504-1.02.968a2.5 2.5 0 1 1-3.237-3.237c.464-.18.894-.527.967-1.02a1.026 1.026 0 0 0-.289-.877l-1.568-1.568A2.402 2.402 0 0 1 1.998 12c0-.617.236-1.234.706-1.704L4.23 8.77c.24-.24.581-.353.917-.303.515.077.877.528 1.073 1.01a2.5 2.5 0 1 0 3.259-3.259c-.482-.196-.933-.558-1.01-1.073-.05-.336.062-.676.303-.917l1.525-1.525A2.402 2.402 0 0 1 12 1.998c.617 0 1.234.236 1.704.706l1.568 1.568c.23.23.556.338.877.29.493-.074.84-.504 1.02-.968a2.5 2.5 0 1 1 3.237 3.237c-.464.18-.894.527-.967 1.02Z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "puzzle" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Refresh_cw = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"
      }
    ],
    ["path", { "d": "M21 3v5h-5" }],
    [
      "path",
      {
        "d": "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"
      }
    ],
    ["path", { "d": "M8 16H3v5" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "refresh-cw" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Search = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "11", "cy": "11", "r": "8" }],
    ["path", { "d": "m21 21-4.3-4.3" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "search" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Send = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "m22 2-7 20-4-9-9-4Z" }], ["path", { "d": "M22 2 11 13" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "send" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Settings = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
      }
    ],
    ["circle", { "cx": "12", "cy": "12", "r": "3" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "settings" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Smartphone = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "14",
        "height": "20",
        "x": "5",
        "y": "2",
        "rx": "2",
        "ry": "2"
      }
    ],
    ["path", { "d": "M12 18h.01" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "smartphone" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Smile = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "M8 14s1.5 2 4 2 4-2 4-2" }],
    [
      "line",
      {
        "x1": "9",
        "x2": "9.01",
        "y1": "9",
        "y2": "9"
      }
    ],
    [
      "line",
      {
        "x1": "15",
        "x2": "15.01",
        "y1": "9",
        "y2": "9"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "smile" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Thumbs_down = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M17 14V2" }],
    [
      "path",
      {
        "d": "M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "thumbs-down" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Thumbs_up = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M7 10v12" }],
    [
      "path",
      {
        "d": "M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "thumbs-up" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Trash_2 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M3 6h18" }],
    [
      "path",
      {
        "d": "M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"
      }
    ],
    [
      "path",
      {
        "d": "M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"
      }
    ],
    [
      "line",
      {
        "x1": "10",
        "x2": "10",
        "y1": "11",
        "y2": "17"
      }
    ],
    [
      "line",
      {
        "x1": "14",
        "x2": "14",
        "y1": "11",
        "y2": "17"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "trash-2" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const User = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"
      }
    ],
    ["circle", { "cx": "12", "cy": "7", "r": "4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "user" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Wifi_off = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "line",
      {
        "x1": "2",
        "x2": "22",
        "y1": "2",
        "y2": "22"
      }
    ],
    ["path", { "d": "M8.5 16.5a5 5 0 0 1 7 0" }],
    ["path", { "d": "M2 8.82a15 15 0 0 1 4.17-2.65" }],
    [
      "path",
      {
        "d": "M10.66 5c4.01-.36 8.14.9 11.34 3.76"
      }
    ],
    [
      "path",
      {
        "d": "M16.85 11.25a10 10 0 0 1 2.22 1.68"
      }
    ],
    ["path", { "d": "M5 13a10 10 0 0 1 5.24-2.76" }],
    [
      "line",
      {
        "x1": "12",
        "x2": "12.01",
        "y1": "20",
        "y2": "20"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "wifi-off" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Wifi = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M5 13a10 10 0 0 1 14 0" }],
    ["path", { "d": "M8.5 16.5a5 5 0 0 1 7 0" }],
    ["path", { "d": "M2 8.82a15 15 0 0 1 20 0" }],
    [
      "line",
      {
        "x1": "12",
        "x2": "12.01",
        "y1": "20",
        "y2": "20"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "wifi" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const TitleBar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $appStore, $$unsubscribe_appStore;
  $$unsubscribe_appStore = subscribe(appStore, (value) => $appStore = value);
  createEventDispatcher();
  $$unsubscribe_appStore();
  return `<header class="h-12 bg-[var(--color-bg-secondary)] border-b border-[var(--color-surface-tertiary)] flex items-center justify-between px-4"><div class="flex items-center gap-3" data-svelte-h="svelte-13t5p9b"><div class="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center"><span class="text-white font-bold text-sm">T</span></div> <span class="text-lg font-semibold text-[var(--color-text-primary)]">TERMIO</span></div> <div class="flex items-center gap-2"><button class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors" title="Sync" ${$appStore.syncState.status === "syncing" ? "disabled" : ""}>${$appStore.syncState.status === "syncing" ? `${validate_component(Refresh_cw, "RefreshCw").$$render($$result, { class: "w-5 h-5 animate-spin" }, {}, {})}` : `${$appStore.syncState.status === "error" ? `${validate_component(Cloud_off, "CloudOff").$$render(
    $$result,
    {
      class: "w-5 h-5 text-[var(--color-error)]"
    },
    {},
    {}
  )}` : `${validate_component(Cloud, "Cloud").$$render($$result, { class: "w-5 h-5" }, {}, {})}`}`}</button> <button class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors" title="Plugins">${validate_component(Puzzle, "Puzzle").$$render($$result, { class: "w-5 h-5" }, {}, {})}</button> <button class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors" title="Device Pairing">${validate_component(Smartphone, "Smartphone").$$render($$result, { class: "w-5 h-5" }, {}, {})}</button> <button class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors" title="Settings">${validate_component(Settings, "Settings").$$render($$result, { class: "w-5 h-5" }, {}, {})}</button></div></header>`;
});
const Sidebar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let filteredConversations;
  let $appStore, $$unsubscribe_appStore;
  $$unsubscribe_appStore = subscribe(appStore, (value) => $appStore = value);
  createEventDispatcher();
  let searchQuery = "";
  filteredConversations = $appStore.conversations.filter((c) => c.title.toLowerCase().includes(searchQuery.toLowerCase()));
  $$unsubscribe_appStore();
  return `<aside class="w-64 bg-[var(--color-bg-secondary)] border-r border-[var(--color-surface-tertiary)] flex flex-col"><div class="p-3"><button class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg transition-colors">${validate_component(Plus, "Plus").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span class="text-sm font-medium" data-svelte-h="svelte-y0kvt8">New Chat</span></button></div> <div class="px-3 pb-3"><div class="relative">${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-tertiary)]"
    },
    {},
    {}
  )} <input type="text" placeholder="Search conversations..." class="w-full pl-9 pr-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--color-accent)]"${add_attribute("value", searchQuery, 0)}></div></div> <div class="flex-1 overflow-y-auto px-2">${each(filteredConversations, (conv) => {
    return `<button class="${"w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors " + escape(
      $appStore.currentConversationId === conv.id ? "bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-primary)]",
      true
    )}">${validate_component(Message_square, "MessageSquare").$$render($$result, { class: "w-4 h-4 flex-shrink-0" }, {}, {})} <span class="flex-1 truncate text-sm">${escape(conv.title)}</span> <button class="p-1 hover:bg-[var(--color-surface-tertiary)] rounded opacity-0 group-hover:opacity-100 transition-opacity">${validate_component(Trash_2, "Trash2").$$render($$result, { class: "w-3 h-3" }, {}, {})}</button> </button>`;
  })} ${filteredConversations.length === 0 ? `<div class="text-center py-8 text-[var(--color-text-tertiary)] text-sm" data-svelte-h="svelte-13r62ej">No conversations yet</div>` : ``}</div></aside>`;
});
const MessageBubble = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { message } = $$props;
  if ($$props.message === void 0 && $$bindings.message && message !== void 0) $$bindings.message(message);
  return `<div class="${"flex gap-4 " + escape(message.role === "user" ? "flex-row-reverse" : "", true)}"><div class="${"w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 " + escape(
    message.role === "user" ? "bg-[var(--color-surface-tertiary)]" : "bg-[var(--color-accent)]",
    true
  )}">${message.role === "user" ? `${validate_component(User, "User").$$render(
    $$result,
    {
      class: "w-4 h-4 text-[var(--color-text-secondary)]"
    },
    {},
    {}
  )}` : `${validate_component(Bot, "Bot").$$render($$result, { class: "w-4 h-4 text-white" }, {}, {})}`}</div> <div class="${"flex-1 max-w-[70%] " + escape(message.role === "user" ? "text-right" : "", true)}"><div class="${"inline-block px-4 py-3 rounded-2xl text-left " + escape(
    message.role === "user" ? "bg-[var(--color-accent)] text-white" : "bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)]",
    true
  )}"><p class="text-sm whitespace-pre-wrap">${escape(message.content)}</p></div> <div class="${"flex items-center gap-2 mt-2 " + escape(message.role === "user" ? "justify-end" : "", true)}"><span class="text-xs text-[var(--color-text-tertiary)]">${escape(new Date(message.timestamp).toLocaleTimeString())}</span> ${message.role === "assistant" ? `<button class="p-1 hover:bg-[var(--color-surface-primary)] rounded transition-colors" title="Copy">${`${validate_component(Copy, "Copy").$$render(
    $$result,
    {
      class: "w-3 h-3 text-[var(--color-text-tertiary)]"
    },
    {},
    {}
  )}`}</button> <button class="p-1 hover:bg-[var(--color-surface-primary)] rounded transition-colors" title="Good response">${validate_component(Thumbs_up, "ThumbsUp").$$render(
    $$result,
    {
      class: "w-3 h-3 text-[var(--color-text-tertiary)]"
    },
    {},
    {}
  )}</button> <button class="p-1 hover:bg-[var(--color-surface-primary)] rounded transition-colors" title="Bad response">${validate_component(Thumbs_down, "ThumbsDown").$$render(
    $$result,
    {
      class: "w-3 h-3 text-[var(--color-text-tertiary)]"
    },
    {},
    {}
  )}</button>` : ``}</div></div></div>`;
});
const ConversationView = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $currentConversation, $$unsubscribe_currentConversation;
  $$unsubscribe_currentConversation = subscribe(currentConversation, (value) => $currentConversation = value);
  let messagesContainer;
  let isTyping = false;
  {
    if ($currentConversation?.messages && messagesContainer) ;
  }
  {
    if ($currentConversation?.messages) {
      const lastMessage = $currentConversation.messages[$currentConversation.messages.length - 1];
      if (lastMessage?.role === "user") {
        isTyping = true;
        setTimeout(() => isTyping = false, 1500);
      }
    }
  }
  $$unsubscribe_currentConversation();
  return `<div class="flex-1 overflow-y-auto"${add_attribute("this", messagesContainer, 0)}>${$currentConversation ? `<div class="max-w-3xl mx-auto py-6 px-4 space-y-4">${each($currentConversation.messages, (message) => {
    return `${validate_component(MessageBubble, "MessageBubble").$$render($$result, { message }, {}, {})}`;
  })} ${isTyping ? `<div class="flex gap-4"><div class="w-8 h-8 rounded-full bg-[var(--color-accent)] flex items-center justify-center flex-shrink-0">${validate_component(Bot, "Bot").$$render($$result, { class: "w-4 h-4 text-white" }, {}, {})}</div> <div class="bg-[var(--color-surface-secondary)] rounded-2xl px-4 py-3" data-svelte-h="svelte-exing9"><div class="flex gap-1"><span class="w-2 h-2 bg-[var(--color-text-tertiary)] rounded-full animate-bounce" style="animation-delay: 0ms"></span> <span class="w-2 h-2 bg-[var(--color-text-tertiary)] rounded-full animate-bounce" style="animation-delay: 150ms"></span> <span class="w-2 h-2 bg-[var(--color-text-tertiary)] rounded-full animate-bounce" style="animation-delay: 300ms"></span></div></div></div>` : ``} ${$currentConversation.messages.length === 0 ? `<div class="text-center py-20">${validate_component(Message_square, "MessageSquare").$$render(
    $$result,
    {
      class: "w-12 h-12 mx-auto text-[var(--color-text-tertiary)] mb-4"
    },
    {},
    {}
  )} <p class="text-[var(--color-text-secondary)]" data-svelte-h="svelte-ln1hkt">Start a conversation</p> <p class="text-[var(--color-text-tertiary)] text-sm mt-1" data-svelte-h="svelte-1pzdhdk">Send a message to begin</p></div>` : ``}</div>` : `<div class="h-full flex items-center justify-center"><div class="text-center">${validate_component(Message_square, "MessageSquare").$$render(
    $$result,
    {
      class: "w-16 h-16 mx-auto text-[var(--color-text-tertiary)] mb-4"
    },
    {},
    {}
  )} <p class="text-[var(--color-text-secondary)] text-lg" data-svelte-h="svelte-vidobf">Welcome to TERMIO</p> <p class="text-[var(--color-text-tertiary)] text-sm mt-1" data-svelte-h="svelte-1n20zlw">Select a conversation or start a new one</p></div></div>`}</div>`;
});
const InputArea = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_currentConversation;
  let $$unsubscribe_appStore;
  $$unsubscribe_currentConversation = subscribe(currentConversation, (value) => value);
  $$unsubscribe_appStore = subscribe(appStore, (value) => value);
  let input = "";
  let isLoading = false;
  $$unsubscribe_currentConversation();
  $$unsubscribe_appStore();
  return `<div class="border-t border-[var(--color-surface-tertiary)] bg-[var(--color-bg-secondary)] p-4"><div class="max-w-3xl mx-auto"><div class="flex items-end gap-3"><button class="p-3 rounded-full bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] transition-colors" title="Attach file">${validate_component(Paperclip, "Paperclip").$$render($$result, { class: "w-5 h-5" }, {}, {})}</button> <div class="flex-1 relative"><textarea placeholder="Type your message..." rows="1" class="w-full px-4 py-3 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-2xl text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] resize-none focus:outline-none focus:border-[var(--color-accent)]">${escape("")}</textarea></div> <div class="relative"><button class="p-3 rounded-full bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] transition-colors" title="Emoji">${validate_component(Smile, "Smile").$$render($$result, { class: "w-5 h-5" }, {}, {})}</button> ${``}</div> <button class="${"p-3 rounded-full transition-colors " + escape(
    "bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]",
    true
  )}"${add_attribute("title", "Start voice input", 0)}>${`${validate_component(Mic, "Mic").$$render($$result, { class: "w-5 h-5" }, {}, {})}`}</button> <button class="p-3 rounded-full bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed" ${!input.trim() || isLoading ? "disabled" : ""}>${`${validate_component(Send, "Send").$$render($$result, { class: "w-5 h-5" }, {}, {})}`}</button></div> <p class="text-center text-xs text-[var(--color-text-tertiary)] mt-2" data-svelte-h="svelte-tcj4dz">Press Enter to send, Shift+Enter for new line</p></div></div>`;
});
const StatusBar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let serverStatus;
  let $appStore, $$unsubscribe_appStore;
  let $unreadNotifications, $$unsubscribe_unreadNotifications;
  $$unsubscribe_appStore = subscribe(appStore, (value) => $appStore = value);
  $$unsubscribe_unreadNotifications = subscribe(unreadNotifications, (value) => $unreadNotifications = value);
  serverStatus = $appStore.serverUrl ? "connected" : "disconnected";
  $$unsubscribe_appStore();
  $$unsubscribe_unreadNotifications();
  return `<footer class="h-8 bg-[var(--color-bg-secondary)] border-t border-[var(--color-surface-tertiary)] flex items-center justify-between px-4 text-xs"><div class="flex items-center gap-4"><div class="flex items-center gap-2">${serverStatus === "connected" ? `${validate_component(Wifi, "Wifi").$$render(
    $$result,
    {
      class: "w-3 h-3 text-[var(--color-success)]"
    },
    {},
    {}
  )} <span class="text-[var(--color-text-tertiary)]" data-svelte-h="svelte-ow49ve">Connected</span>` : `${validate_component(Wifi_off, "WifiOff").$$render(
    $$result,
    {
      class: "w-3 h-3 text-[var(--color-error)]"
    },
    {},
    {}
  )} <span class="text-[var(--color-text-tertiary)]" data-svelte-h="svelte-8jf99y">Offline</span>`}</div> <div class="flex items-center gap-2">${validate_component(Hard_drive, "HardDrive").$$render(
    $$result,
    {
      class: "w-3 h-3 text-[var(--color-text-tertiary)]"
    },
    {},
    {}
  )} <span class="text-[var(--color-text-tertiary)]" data-svelte-h="svelte-vus01y">Local</span></div></div> <div class="flex items-center gap-4"><button class="flex items-center gap-2 hover:text-[var(--color-text-primary)] transition-colors">${validate_component(Bell, "Bell").$$render($$result, { class: "w-3 h-3" }, {}, {})} <span class="text-[var(--color-text-tertiary)]">${$unreadNotifications > 0 ? `${escape($unreadNotifications)} notifications` : `No notifications`}</span></button> <span class="text-[var(--color-text-tertiary)]" data-svelte-h="svelte-1rpa03x">TERMIO v2.0.0</span></div></footer>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_appStore;
  $$unsubscribe_appStore = subscribe(appStore, (value) => value);
  $$unsubscribe_appStore();
  return `<div class="h-screen flex flex-col bg-[var(--color-bg-primary)]">${validate_component(TitleBar, "TitleBar").$$render($$result, {}, {}, {})} <div class="flex-1 flex overflow-hidden">${validate_component(Sidebar, "Sidebar").$$render($$result, {}, {}, {})} <main class="flex-1 flex flex-col">${validate_component(ConversationView, "ConversationView").$$render($$result, {}, {}, {})} ${validate_component(InputArea, "InputArea").$$render($$result, {}, {}, {})}</main></div> ${validate_component(StatusBar, "StatusBar").$$render($$result, {}, {}, {})}</div> ${``} ${``} ${``}`;
});
export {
  Page as default
};
