export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {start:"_app/immutable/entry/start.BU73cOAC.js",app:"_app/immutable/entry/app.BnhaFSQG.js",imports:["_app/immutable/entry/start.BU73cOAC.js","_app/immutable/chunks/LkcnRoe0.js","_app/immutable/chunks/myKowI8s.js","_app/immutable/chunks/8BKlv0Op.js","_app/immutable/entry/app.BnhaFSQG.js","_app/immutable/chunks/C1FmrZbK.js","_app/immutable/chunks/myKowI8s.js","_app/immutable/chunks/CK5bAZH2.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
