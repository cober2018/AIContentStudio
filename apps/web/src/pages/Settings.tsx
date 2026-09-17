import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, currentUser, setCurrentUser } from "../api";

interface Me {
  id: number;
  email: string;
  name: string;
  role: string;
}

interface UserRow {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

const ROLE_DESC: Record<string, string> = {
  admin: "系统/模型/模板/品牌/用户，全部权限",
  editor: "Source、FactPack、生成、审核提交",
  reviewer: "审核与改稿",
  viewer: "只读",
};

export default function Settings() {
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: () => api.get<UserRow[]>("/users") });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/users/me") });
  const [selected, setSelected] = useState(currentUser());

  useEffect(() => {
    if (me) setSelected(me.email);
  }, [me]);

  function switchUser(email: string) {
    setCurrentUser(email);
    setSelected(email);
    window.location.reload();
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <h1 className="text-xl font-semibold">设置</h1>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-medium">当前身份（开发模式）</h2>
        <p className="mt-1 text-xs text-slate-400">
          V1 使用 Header 身份便于演示 RBAC；生产部署替换为标准身份框架（见 README）。
        </p>
        {me && (
          <div className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
            {me.name} · {me.email} · <span className="font-medium text-indigo-600">{me.role}</span>
          </div>
        )}
        <div className="mt-3 flex flex-wrap gap-2">
          {(users || []).map((u) => (
            <button
              key={u.email}
              onClick={() => switchUser(u.email)}
              className={`rounded-md border px-3 py-1.5 text-xs ${
                selected === u.email
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {u.role} · {u.email}
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-medium">角色权限矩阵</h2>
        <div className="mt-3 space-y-2">
          {Object.entries(ROLE_DESC).map(([role, desc]) => (
            <div key={role} className="flex gap-3 text-sm">
              <span className="w-20 shrink-0 font-mono text-xs text-indigo-600">{role}</span>
              <span className="text-slate-600">{desc}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-medium">模型 Provider</h2>
        <p className="mt-1 text-xs text-slate-400">
          通过环境变量配置（.env）：LLM_PROVIDER=mock | openai_compatible，LLM_BASE_URL / LLM_API_KEY /
          LLM_MODEL。Secret 不入库。
        </p>
        <p className="mt-2 text-xs text-slate-400">
          mock provider 用于原型与测试；设置 MOCK_INJECT_UNFACT_NUMBER=true 可注入无来源数字验证 FactCheck 链路。
        </p>
      </section>
    </div>
  );
}
