<template>
  <!-- ═══ 项目列表页（无打开项目时） ═══ -->
  <div v-if="!proj" class="min-h-screen" style="background:var(--bg-canvas);color:var(--text-primary)">
    <header class="h-14 px-5 flex items-center justify-between shrink-0" style="background:var(--bg-surface-1)">
      <div class="flex items-center gap-3">
        <button @click="$router.push('/workspace')" class="transition" style="color:var(--text-tertiary)" onmouseover="this.style.color='var(--text-primary)'" onmouseout="this.style.color='var(--text-tertiary)'">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <h1 class="text-sm font-semibold tracking-wide" style="color:var(--text-primary)">一键成片</h1>
      </div>
      <button @click="showCreate = true" class="h-8 px-4 rounded-lg text-xs font-medium transition" style="background:var(--accent)" onmouseover="this.style.background='var(--accent-hover)'" onmouseout="this.style.background='var(--accent)'">
        + 新建项目
      </button>
    </header>

    <div class="max-w-5xl mx-auto p-8">
      <div v-if="loading" class="text-center py-20 text-sm" style="color:var(--text-muted)">加载中...</div>
      <div v-else-if="projects.length === 0" class="text-center py-20">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center" style="background:var(--bg-surface-2)">
          <svg class="w-7 h-7" style="color:var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
        </div>
        <p class="text-sm mb-4" style="color:var(--text-muted)">还没有项目</p>
        <button @click="showCreate = true" class="px-5 py-2.5 rounded-lg text-sm font-medium transition" style="background:var(--accent)" onmouseover="this.style.background='var(--accent-hover)'" onmouseout="this.style.background='var(--accent)'">创建第一个项目</button>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="p in projects" :key="p.id"
          class="group rounded-xl p-4 transition-all cursor-pointer project-card"
          style="background:var(--bg-surface-2)"
          @click="openProject(p)">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-medium text-sm truncate transition" style="color:var(--text-primary)">{{ p.name }}</h3>
            <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="phaseClass(p.phase)">{{ phaseLabel(p.phase) }}</span>
          </div>
          <div class="text-xs space-y-0.5" style="color:var(--text-muted)">
            <p>{{ p.video_model }} · {{ p.ratio }} · {{ p.segments_count ? p.segments_count + '段×' + p.duration + 's=' + (p.segments_count * p.duration) + 's' : p.duration + 's/段' }}</p>
            <div class="flex gap-1.5 mt-1.5">
              <span v-if="p.assets_count" class="px-1.5 py-0.5 rounded stat-tag-accent">{{ p.phase2_done || 0 }}/{{ p.assets_count }} 资产</span>
              <span v-if="p.segments_count" class="px-1.5 py-0.5 rounded stat-tag-accent">{{ p.phase3_done || 0 }}/{{ p.segments_count }} 故事板</span>
              <span v-if="p.segments_count" class="px-1.5 py-0.5 rounded stat-tag-success">{{ p.phase4_done || 0 }}/{{ p.segments_count }} 视频</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 新建项目弹窗 ═══ -->
    <div v-if="showCreate" class="fixed inset-0 flex items-center justify-center z-50 p-4" style="background:color-mix(in srgb, var(--bg-canvas) 60%, transparent)" @click.self="showCreate = false">
      <div class="rounded-2xl p-6 w-full max-w-md" style="background:var(--bg-surface-2)">
        <h2 class="text-base font-semibold mb-5" style="color:var(--text-primary)">新建项目</h2>
        <div class="space-y-3">
          <div>
            <label class="lbl">项目名称</label>
            <input v-model="createForm.name" class="inp" placeholder="例：五旬老太重生记 Ep1" />
          </div>
          <div>
            <label class="lbl">原始剧本 <span style="color:var(--text-tertiary)">（可选，粘贴或上传txt）</span></label>
            <div class="flex gap-2 items-start">
              <textarea v-model="createForm.raw_script" class="inp flex-1 resize-none" rows="5" placeholder="粘贴剧本内容..."></textarea>
              <label class="shrink-0 h-[104px] flex flex-col items-center justify-center rounded-lg px-3 cursor-pointer transition" style="background:var(--bg-surface-3);border:1px solid var(--border-hairline)">
                <svg class="w-4 h-4 mb-1" style="color:var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                <span class="text-[10px]" style="color:var(--text-tertiary)">上传</span>
                <input type="file" accept=".txt,.md,.text" class="hidden" @change="uploadScript" />
              </label>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="lbl">视频模型</label><select v-model="createForm.video_model" class="sel">
              <option value="Gemini Omni">Gemini Omni</option><option value="Grok Imagine">Grok Imagine</option>
              <option value="Vidu Q3 Pro">Vidu Q3 Pro</option><option value="Kling 2.6">Kling 2.6</option>
              <option value="Wan2.7">Wan2.7</option><option value="Seedance 1.5 Pro">Seedance 1.5 Pro</option>
            </select></div>
            <div><label class="lbl">图片模型</label><select v-model="createForm.image_model" class="sel">
              <option value="GPT-Image2">GPT Image 2</option><option value="Seedream 5.0">Seedream 5.0</option>
              <option value="Flux">Flux</option><option value="Niji7">Niji7</option>
            </select></div>
          </div>
          <div class="grid grid-cols-4 gap-3">
            <div><label class="lbl">比例</label><select v-model="createForm.ratio" class="sel">
              <option value="16:9">16:9</option><option value="9:16">9:16</option><option value="1:1">1:1</option>
            </select></div>
            <div><label class="lbl">视频分辨率</label><select v-model="createForm.resolution" class="sel">
              <option value="720p">720p</option><option value="1080p">1080p</option><option value="4K">4K</option>
            </select></div>
            <div><label class="lbl">图片分辨率</label><select v-model="createForm.image_resolution" class="sel">
              <option value="1K">1K</option><option value="2K">2K</option><option value="4K">4K</option>
            </select></div>
            <div><label class="lbl">时长/段</label><select v-model="createForm.duration" class="sel">
              <option :value="5">5s</option><option :value="6">6s</option><option :value="8">8s</option><option :value="10">10s</option>
            </select></div>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-5">
          <button @click="showCreate = false" class="px-4 py-2 text-xs transition" style="color:var(--text-muted)">取消</button>
          <button @click="createProject" class="px-5 py-2 rounded-lg text-xs font-medium transition" style="background:var(--accent)" onmouseover="this.style.background='var(--accent-hover)'" onmouseout="this.style.background='var(--accent)'" :disabled="!createForm.name || creating">
            {{ creating ? '...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══ 项目详情页：左右并排布局 ═══ -->
  <div v-else class="h-screen flex flex-col" style="background:var(--bg-canvas)">
    <!-- 顶栏 -->
    <div class="h-10 shrink-0 flex items-center gap-3 px-4" style="background:var(--bg-surface-1)">
      <button @click="closeProject" class="text-xs transition" style="color:var(--text-tertiary)">← 返回</button>
      <span class="text-xs font-semibold truncate max-w-[200px]" style="color:var(--text-primary)">{{ proj.name }}</span>
      <button @click="scriptModal=true" class="px-2 py-0.5 text-[10px] rounded transition" style="color:var(--text-tertiary);background:var(--bg-surface-3)">剧本</button>
      <div class="flex-1"></div>
      <button @click="saveScript" class="px-2 py-0.5 text-[10px] rounded transition" style="color:var(--text-tertiary);background:var(--bg-surface-3)" :disabled="savingScript">{{ savingScript ? '...' : '保存' }}</button>
      <span v-if="saveNotification" class="text-[10px] animate-pulse" style="color: var(--color-success)">{{ saveNotification }}</span>
      <button @click="deleteProject" class="px-2 py-0.5 text-[10px] rounded transition" style="color: var(--color-error);background:var(--bg-surface-3)">删除</button>
      <button @click="showAgent=!showAgent" class="px-2 py-0.5 text-[10px] rounded transition" :style="showAgent?'color: var(--accent)':'color: var(--text-tertiary)'" style="background:var(--bg-surface-3)">💬Agent</button>
    </div>

    <!-- 工作流进度条 -->
    <div class="h-9 shrink-0 flex items-center gap-1 px-4" style="background:var(--bg-surface-1)">
      <div v-for="(step, idx) in workflowSteps" :key="idx" class="flex items-center gap-1">
        <div v-if="idx > 0" class="w-4 h-px" :style="step.status==='pending'?'background:var(--bg-surface-3)':'background:var(--color-success)'"></div>
        <div class="flex items-center gap-1 px-2 py-0.5 rounded" :style="step.status==='done'?'background:color-mix(in srgb, var(--color-success) 10%, transparent)':step.status==='running'?'background:var(--accent-subtle)':'background:var(--bg-surface-1)'">
          <span class="w-4 h-4 rounded-full text-[8px] font-bold flex items-center justify-center shrink-0"
            :style="step.status==='done'?'background:color-mix(in srgb, var(--color-success) 30%, transparent);color:var(--color-success)':step.status==='running'?'background:var(--accent-glow);color:var(--accent)':'background:var(--bg-surface-3);color:var(--text-tertiary)'">
            <template v-if="step.status==='done'">✓</template><template v-else>{{ idx+1 }}</template>
          </span>
          <span class="text-[9px] font-medium" :style="step.status==='done'?'color:var(--color-success)':step.status==='running'?'color:var(--accent)':'color:var(--text-tertiary)'">{{ step.label }}</span>
          <button v-if="step.action && step.status!=='done'" @click="step.actionFn" class="text-[8px] px-1 py-0.5 rounded transition shrink-0" style="background:var(--accent-subtle);color:var(--accent)" :disabled="step.actionDisabled">{{ step.actionDisabled?'...':step.action }}</button>
        </div>
      </div>
    </div>

    <!-- 主内容区：四列并排 -->
    <div class="flex-1 flex min-h-0">

      <!-- ─── 资产列 ─── -->
      <div class="flex flex-col transition-all" :style="{width: assetCollapsed ? '48px' : '20%', background: 'var(--bg-surface-1)'}">
        <div class="px-2 py-2 flex items-center justify-between">
          <span v-if="!assetCollapsed" class="text-[11px] font-semibold uppercase tracking-wider" style="color:var(--text-muted)">资产 ({{editAssets.length}})</span>
          <div v-if="!assetCollapsed" class="flex gap-1">
            <button v-if="editAssets.length" @click="generateAllAssets" class="text-[9px]" style="color: var(--accent)" :disabled="generatingAllAssets">{{ generatingAllAssets?'生成中...':'全部生成' }}</button>
            <button @click="addAsset" class="text-[9px]" style="color:var(--text-tertiary)">+</button>
            <button @click="assetCollapsed=!assetCollapsed" class="text-[10px]" style="color:var(--text-tertiary)">◂</button>
          </div>
          <button v-if="assetCollapsed" @click="assetCollapsed=!assetCollapsed" class="text-[10px]" style="color:var(--text-tertiary)">▸</button>
        </div>
        <div v-if="!assetCollapsed" class="flex-1 overflow-y-auto p-2 space-y-1">
          <div v-for="(a, i) in editAssets" :key="'a'+i"
               class="flex items-center gap-2 px-2 py-1.5 rounded-lg transition group asset-item"
               style="background:var(--bg-surface-2)">
            <!-- 缩略图 40x40 -->
            <div class="w-10 h-10 shrink-0 rounded bg-black/30 cursor-pointer relative"
                 @click="uploadAssetRef(i)">
              <img v-if="a.reference_image || getAssetResultImage(i)"
                   :src="getUrl(a.reference_image || getAssetResultImage(i))"
                   class="w-full h-full object-cover rounded"
                   @mouseenter="showPreview(a.reference_image || getAssetResultImage(i), $event)"
                   @mouseleave="hidePreview()"
                   @mousemove="showPreview(a.reference_image || getAssetResultImage(i), $event)" />
              <div v-else class="w-full h-full flex items-center justify-center">
                <svg class="w-4 h-4" style="color:var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4"/></svg>
              </div>
              <div v-if="isAssetGenerating(i)" class="absolute inset-0 bg-black/50 flex items-center justify-center rounded">
                <div class="dot-spin"></div>
              </div>
              <div v-if="getAssetResultImage(i)" class="absolute top-0 right-0 w-1.5 h-1.5 rounded-full" style="background: var(--color-success)"></div>
              <input type="file" :ref="(el:any) => assetFileInputs[i] = el" class="hidden" accept="image/*" @change="handleAssetRefUpload($event, i)" />
            </div>
            <!-- 信息 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1">
                <input v-model="a.name" class="bg-transparent text-[11px] font-medium flex-1 min-w-0 focus:outline-none truncate" style="color:var(--text-primary)" placeholder="资产名" />
                <select v-model="a.type" class="text-[8px] rounded px-0.5 py-0 focus:outline-none shrink-0" style="background:var(--bg-surface-3);color:var(--text-muted)">
                  <option value="角色">角色</option><option value="场景">场景</option><option value="道具">道具</option>
                </select>
                <span v-if="a.type==='角色' && a.is_primary===false" class="text-[7px] px-1 py-0 rounded-full shrink-0" style="background:color-mix(in srgb, var(--color-warning) 15%, transparent);color:var(--color-warning)">衍生</span>
              </div>
              <!-- 角色多形态字段 -->
              <div v-if="a.type==='角色'" class="flex items-center gap-1 mt-0.5">
                <label class="flex items-center gap-0.5 cursor-pointer shrink-0">
                  <input type="checkbox" v-model="a.is_primary" class="w-2 h-2" style="accent-color: var(--accent)" />
                  <span class="text-[8px]" style="color:var(--text-tertiary)">主形态</span>
                </label>
                <select v-if="a.is_primary===false" v-model="a.reference_form" class="text-[8px] rounded px-0.5 py-0 focus:outline-none flex-1 min-w-0" style="background:var(--bg-surface-3);color:var(--text-muted)">
                  <option value="">选择参考</option>
                  <option v-for="pa in getPrimaryCharacters(i)" :key="pa.name" :value="pa.name">{{ pa.name }}</option>
                </select>
              </div>
              <div class="flex items-center gap-1 mt-0.5">
                <button @click="generateSingleAsset(i)" class="text-[9px]" style="color: var(--accent)" :disabled="isAssetGenerating(i)||generatingAsset">{{ isAssetGenerating(i)||generatingAsset?'...':'生成' }}</button>
                <button @click="uploadAssetResult(i)" class="text-[9px]" style="color:var(--text-tertiary)">上传</button>
                <button @click="toggleAssetPromptEdit(i)" class="text-[9px]" style="color:var(--text-tertiary)">✎prompt</button>
                <button @click="confirmDeleteAsset(i)" class="text-[9px] ml-auto" style="color:var(--color-error)">x</button>
              </div>
              <!-- 资产prompt显示（截断2行，点击展开） -->
              <div v-if="getAssetPrompt(i) && editingAssetPrompt!==i" class="mt-0.5 px-1 py-0.5 rounded text-[8px] line-clamp-2 cursor-pointer prompt-mini-display" style="color:var(--text-muted);background:var(--bg-surface-3)" @click="toggleAssetPromptEdit(i)">
                {{ getAssetPrompt(i) }}
              </div>
              <!-- 资产prompt编辑区 -->
              <div v-if="editingAssetPrompt===i" class="mt-0.5 space-y-0.5">
                <textarea v-model="assetPromptEdits[i]" class="w-full rounded px-1.5 py-0.5 text-[9px] focus:outline-none resize-none prompt-edit-input" rows="2" :placeholder="getAssetPrompt(i)||'输入prompt...'"></textarea>
                <div class="flex justify-end gap-1">
                  <button @click="editingAssetPrompt=-1" class="text-[8px]" style="color:var(--text-muted)">取消</button>
                  <button @click="saveAssetPromptAndRegenerate(i)" class="text-[8px] px-1 py-0.5 rounded" style="background:var(--accent);color:var(--text-primary)" :disabled="isAssetGenerating(i)||generatingAsset">用此prompt重新生成</button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="!editAssets.length" class="text-center py-6 text-[10px]" style="color:var(--text-tertiary)">暂无资产，点击 + 添加</div>
        </div>
        <div v-else class="flex-1 flex flex-col items-center pt-2 space-y-1">
          <span class="text-[9px] writing-vertical" style="color:var(--text-tertiary)">{{ editAssets.length }}资产</span>
        </div>
      </div>

      <!-- ─── 分镜列 ─── -->
      <div class="flex flex-col" style="width:25%;background:var(--bg-canvas)">
        <div class="px-3 py-2 flex items-center justify-between">
          <span class="text-[11px] font-semibold uppercase tracking-wider" style="color:var(--text-muted)">分镜 ({{editSegments.length}}段)</span>
          <div class="flex gap-1">
            <button v-if="editSegments.length" @click="generateAllStoryboards" class="text-[9px]" style="color: var(--accent)" :disabled="generatingAllStoryboards">{{ generatingAllStoryboards?'生成中...':'全部故事板' }}</button>
            <button @click="addSegment" class="text-[9px]" style="color:var(--text-tertiary)">+</button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
          <div v-for="(seg, si) in editSegments" :key="'s'+si"
               class="rounded-lg overflow-hidden segment-item"
               style="background:var(--bg-surface-2)">
            <!-- 段头部 一行 -->
            <div class="flex items-center gap-2 px-2 py-1.5 cursor-pointer" style="transition:background 0.15s" @click="seg._open=!seg._open">
              <svg class="w-2.5 h-2.5 transition-transform shrink-0" :class="seg._open?'rotate-90':''" style="color:var(--text-tertiary)" fill="currentColor" viewBox="0 0 20 20"><path d="M6 4l8 6-8 6V4z"/></svg>
              <input v-model="seg.title" class="bg-transparent text-[11px] font-medium flex-1 focus:outline-none" style="color:var(--text-primary)" placeholder="段标题" @click.stop />
              <span class="text-[9px] shrink-0" style="color:var(--text-tertiary)">{{ seg.shots?.length||0 }}镜</span>
              <!-- 故事板缩略图 -->
              <div v-if="getSegStoryboardImage(si)" class="w-8 h-6 rounded shrink-0 overflow-hidden" style="border:1px solid var(--border-hairline)">
                <img :src="getUrl(getSegStoryboardImage(si))" class="w-full h-full object-cover"
                     @mouseenter="showPreview(getSegStoryboardImage(si), $event)"
                     @mouseleave="hidePreview()"
                     @mousemove="showPreview(getSegStoryboardImage(si), $event)" />
              </div>
              <span v-if="getSegStoryboardStatus(si)" class="text-[8px] shrink-0" :style="getSegStoryboardStatus(si)==='completed'?'color:var(--color-success)':getSegStoryboardStatus(si)==='running'?'color:var(--accent)':'color:var(--text-tertiary)'">
                {{ getSegStoryboardStatus(si)==='completed'?'✓':getSegStoryboardStatus(si)==='running'?'...':'✗' }}
              </span>
              <button @click.stop="generateSingleStoryboard(si)" class="px-1.5 py-0.5 rounded text-[8px] font-medium shrink-0 transition" style="background:var(--accent);color:var(--text-primary)" :disabled="isSegStoryboardGenerating(si)">{{ isSegStoryboardGenerating(si)?'...':'故事板' }}</button>
              <button @click.stop="confirmDeleteSegment(si)" class="text-[9px] shrink-0" style="color:var(--color-error)">x</button>
            </div>
            <!-- 展开内容 -->
            <div v-if="seg._open" class="px-2 pb-2 space-y-1" style="border-top:1px solid var(--border-hairline)">
              <!-- 引用资产 -->
              <div class="pt-1.5 flex items-center gap-1 flex-wrap">
                <span class="text-[8px]" style="color:var(--text-tertiary)">引用:</span>
                <label v-for="(a, ai) in editAssets" :key="'ref'+ai" class="flex items-center gap-0.5 cursor-pointer">
                  <input type="checkbox" :value="ai" v-model="seg.assets" class="w-2 h-2" style="accent-color: var(--accent)" />
                  <span class="text-[8px]" style="color:var(--text-tertiary)">{{ a.name || '资产'+(ai+1) }}</span>
                </label>
                <span v-if="!editAssets.length" class="text-[8px]" style="color:var(--text-tertiary)">暂无资产</span>
              </div>
              <!-- 故事板prompt显示与编辑 -->
              <div v-if="getStoryboardPrompt(si) || getSegStoryboardImage(si)" class="pt-1">
                <div class="flex items-center gap-1 mb-0.5">
                  <span class="text-[8px]" style="color:var(--text-tertiary)">故事板Prompt</span>
                  <button @click="toggleStoryboardPromptEdit(si)" class="text-[8px]" style="color:var(--accent)">✎编辑</button>
                </div>
                <div v-if="getStoryboardPrompt(si) && editingStoryboardPrompt!==si" class="px-1.5 py-1 rounded text-[8px] line-clamp-2 cursor-pointer prompt-mini-display" style="color:var(--text-muted);background:var(--bg-surface-3)" @click="toggleStoryboardPromptEdit(si)">
                  {{ getStoryboardPrompt(si) }}
                </div>
                <div v-if="editingStoryboardPrompt===si" class="space-y-0.5">
                  <textarea v-model="storyboardPromptEdits[si]" class="w-full rounded px-1.5 py-0.5 text-[9px] focus:outline-none resize-none prompt-edit-input" rows="2" :placeholder="getStoryboardPrompt(si)||'输入故事板prompt...'"></textarea>
                  <div class="flex justify-end gap-1">
                    <button @click="editingStoryboardPrompt=-1" class="text-[8px]" style="color:var(--text-muted)">取消</button>
                    <button @click="saveStoryboardPromptAndRegenerate(si)" class="text-[8px] px-1 py-0.5 rounded" style="background:var(--accent);color:var(--text-primary)" :disabled="isSegStoryboardGenerating(si)||generatingStoryboard">用此prompt重新生成</button>
                  </div>
                </div>
              </div>
              <!-- 镜头列表 -->
              <div v-for="(sh, shi) in seg.shots" :key="'sh'+shi" class="py-0.5 space-y-0.5">
                <div class="flex items-center gap-1">
                  <span class="text-[8px] w-5 shrink-0" style="color:var(--text-tertiary)">{{ shi+1 }}</span>
                  <input v-model="sh.visual" class="shot-input flex-1 rounded px-1 py-0.5 text-[10px] focus:outline-none min-w-0" placeholder="画面" />
                </div>
                <div class="flex items-center gap-1 pl-5">
                  <input v-model="sh.camera" class="shot-input w-14 rounded px-1 py-0.5 text-[10px] focus:outline-none shrink-0" placeholder="运镜" />
                  <input v-model="sh.lighting" class="shot-input w-14 rounded px-1 py-0.5 text-[10px] focus:outline-none shrink-0" placeholder="光线" />
                  <input v-model="sh.audio" class="shot-input w-14 rounded px-1 py-0.5 text-[10px] focus:outline-none shrink-0" placeholder="音效" />
                  <input v-model="sh.dialogue" class="shot-input w-16 rounded px-1 py-0.5 text-[10px] focus:outline-none shrink-0" placeholder="台词" />
                  <select v-model="sh.transition" class="shot-input w-16 rounded px-1 py-0.5 text-[10px] focus:outline-none shrink-0" style="color:var(--text-muted)">
                    <option value="cut">[cut]</option><option value="dissolve">[dissolve]</option><option value="camera_push">[camera_push]</option><option value="camera_pan">[camera_pan]</option><option value="fade_black">[fade_black]</option><option value="end">[end]</option>
                  </select>
                  <button @click="confirmDeleteShot(seg,shi)" class="text-[8px] shrink-0" style="color:var(--color-error)">x</button>
                </div>
              </div>
              <button @click="addShot(seg)" class="text-[9px]" style="color:var(--text-tertiary)">+ 镜头</button>
            </div>
          </div>
          <div v-if="!editSegments.length" class="text-center py-6 text-[10px]" style="color:var(--text-tertiary)">暂无分镜段，请先AI拆段</div>
        </div>
      </div>

      <!-- ─── 视频列 ─── -->
      <div class="flex flex-col" :style="{width: assetCollapsed ? '75%' : '55%', background: 'var(--bg-canvas)'}">
        <div class="px-3 py-2 flex items-center justify-between">
          <span class="text-[11px] font-semibold uppercase tracking-wider" style="color:var(--text-muted)">视频 ({{videoDoneCount}}/{{editSegments.length}})</span>
          <div class="flex gap-1">
            <button v-if="editSegments.length" @click="generateAllVideos" class="text-[9px]" style="color: var(--accent)" :disabled="generatingAllVideos">{{ generatingAllVideos?'生成中...':'全部生成' }}</button>
            <button v-if="editSegments.length && videoDoneCount > 0" @click="regenerateAllVideos" class="text-[9px]" style="color: var(--color-warning)" :disabled="generatingAllVideos">重新全部生成</button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-2">
          <!-- 视频网格 -->
          <div class="video-grid">
            <div v-for="(seg, si) in editSegments" :key="'v'+si" class="video-card" @click="openVideoLightbox(si)">
              <!-- 缩略图区域 -->
              <div class="video-card-thumb" :style="{aspectRatio: isPortrait ? '9/16' : '16/9'}">
                <!-- 有视频：显示缩略图+播放按钮 -->
                <template v-if="getVideoUrl(si)">
                  <video :src="getUrl(getVideoUrl(si))" preload="metadata" muted class="video-card-video" />
                  <div class="play-overlay">▶</div>
                </template>
                <!-- 生成中 -->
                <div v-else-if="isVideoGenerating(si)" class="loading-state">
                  <div class="dot-spin"></div>
                  <span class="text-[9px] mt-1" style="color:var(--text-muted)">生成中</span>
                </div>
                <!-- 失败 -->
                <div v-else-if="getVideoStatus(si)==='failed'" class="error-state" @click.stop="retryItem(4,si)">
                  <span class="text-[10px]" style="color:var(--color-error)">✗</span>
                  <span class="text-[8px]" style="color:var(--color-error)">重试</span>
                </div>
                <!-- 未生成 -->
                <div v-else class="empty-state" @click.stop="generateSingleVideo(si)">
                  <svg class="w-5 h-5" style="color:var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span class="text-[8px]" style="color:var(--text-tertiary)">生成</span>
                </div>
                <!-- 段标题覆盖在底部 -->
                <div class="video-card-title-overlay">{{ seg.title || '段'+(si+1) }}</div>
                <!-- 状态徽标 -->
                <div v-if="getVideoStatus(si)==='completed'" class="video-card-status status-done">✓</div>
                <div v-else-if="getVideoStatus(si)==='running'" class="video-card-status status-running">…</div>
                <div v-else-if="getVideoStatus(si)==='failed'" class="video-card-status status-failed">✗</div>
              </div>
            </div>
          </div>
          <div v-if="!editSegments.length" class="text-center py-6 text-[10px]" style="color:var(--text-tertiary)">暂无分镜段，请先AI拆段</div>
        </div>
      </div>

      <!-- ─── 视频灯箱 ─── -->
      <div v-if="videoLightbox !== -1" class="video-lightbox-overlay" @click.self="videoLightbox=-1">
        <div class="video-lightbox-content">
          <button class="lightbox-close" @click="videoLightbox=-1">✕</button>
          <!-- 视频播放器 -->
          <div class="lightbox-player">
            <template v-if="getVideoUrl(videoLightbox)">
              <video :src="getUrl(getVideoUrl(videoLightbox))" controls autoplay class="lightbox-video" :style="{aspectRatio: isPortrait ? '9/16' : '16/9'}" />
            </template>
            <div v-else-if="isVideoGenerating(videoLightbox)" class="lightbox-loading">
              <div class="dot-spin" style="width:24px;height:24px;border-width:3px"></div>
              <span class="text-xs mt-2" style="color:var(--text-muted)">生成中...</span>
            </div>
            <div v-else class="lightbox-empty">
              <span class="text-sm" style="color:var(--text-tertiary)">暂无视频</span>
            </div>
          </div>
          <!-- 信息区 -->
          <div class="lightbox-info">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-sm font-medium truncate" style="color:var(--text-primary)">{{ editSegments[videoLightbox]?.title || '段'+(videoLightbox+1) }}</h3>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="getVideoStatus(videoLightbox)" class="text-[9px]" :style="getVideoStatus(videoLightbox)==='completed'?'color:var(--color-success)':getVideoStatus(videoLightbox)==='running'?'color:var(--accent)':'color:var(--text-tertiary)'">
                  {{ getVideoStatus(videoLightbox)==='completed'?'完成':getVideoStatus(videoLightbox)==='running'?'生成中':getVideoStatus(videoLightbox)==='failed'?'失败':'—' }}
                </span>
              </div>
            </div>
            <!-- 参考图 -->
            <div v-if="getSegStoryboardImage(videoLightbox) || getSegRefImages(videoLightbox).length" class="flex gap-1 mb-2 overflow-x-auto pb-1" style="scrollbar-width:thin">
              <div v-if="getSegStoryboardImage(videoLightbox)" class="h-12 w-12 shrink-0 rounded overflow-hidden" style="border:1px solid var(--border-hairline)">
                <img :src="getUrl(getSegStoryboardImage(videoLightbox))" class="h-full w-full object-cover" />
              </div>
              <div v-for="(rimg, ri) in getSegRefImages(videoLightbox)" :key="'lri'+ri" class="h-12 w-12 shrink-0 rounded overflow-hidden" style="border:1px solid var(--border-hairline)">
                <img :src="getUrl(rimg)" class="h-full w-full object-cover" />
              </div>
            </div>
            <!-- 垫图选择器 -->
            <div class="mb-2">
              <div class="flex items-center justify-between mb-1">
                <div class="text-[9px] font-medium" style="color:var(--text-muted)">垫图 (点击选择项目图片)</div>
                <button @click="showRefPicker=!showRefPicker" class="text-[9px] px-1.5 py-0.5 rounded" style="background:var(--accent-subtle);color:var(--accent)">{{ showRefPicker ? '收起' : '+ 选择垫图' }}</button>
              </div>
              <!-- 已选垫图 -->
              <div v-if="selectedRefImages.length" class="flex gap-1 mb-1 overflow-x-auto pb-1" style="scrollbar-width:thin">
                <div v-for="(rimg, ri) in selectedRefImages" :key="'sr'+ri" class="relative h-10 w-10 shrink-0 rounded overflow-hidden" style="border:1px solid var(--accent)">
                  <img :src="getUrl(rimg)" class="h-full w-full object-cover" />
                  <button @click="selectedRefImages.splice(ri,1)" class="absolute top-0 right-0 w-3.5 h-3.5 flex items-center justify-center text-[8px] rounded-bl" style="background:var(--color-error);color:white">✕</button>
                </div>
              </div>
              <!-- 垫图选择面板 -->
              <div v-if="showRefPicker" class="p-2 rounded-lg max-h-40 overflow-y-auto" style="background:var(--bg-surface-2);scrollbar-width:thin">
                <div class="grid grid-cols-4 gap-1.5">
                  <!-- 资产图 -->
                  <div v-for="(ast, ai) in editAssets" :key="'ra'+ai">
                    <div v-if="getAssetResultImage(ai)" @click="toggleRefImage(getAssetResultImage(ai)!)"
                         class="h-12 rounded cursor-pointer overflow-hidden relative" :style="{border: selectedRefImages.includes(getAssetResultImage(ai)!) ? '2px solid var(--accent)' : '1px solid var(--border-hairline)'}">
                      <img :src="getUrl(getAssetResultImage(ai)!)" class="h-full w-full object-cover" />
                      <div class="absolute bottom-0 left-0 right-0 px-0.5 py-0 text-[6px] truncate" style="background:color-mix(in srgb, var(--bg-canvas) 70%, transparent);color:var(--text-secondary)">{{ ast.name }}</div>
                    </div>
                  </div>
                  <!-- 故事板图 -->
                  <div v-for="(_, si) in editSegments" :key="'rs'+si">
                    <div v-if="getSegStoryboardImage(si)" @click="toggleRefImage(getSegStoryboardImage(si)!)"
                         class="h-12 rounded cursor-pointer overflow-hidden relative" :style="{border: selectedRefImages.includes(getSegStoryboardImage(si)!) ? '2px solid var(--accent)' : '1px solid var(--border-hairline)'}">
                      <img :src="getUrl(getSegStoryboardImage(si)!)" class="h-full w-full object-cover" />
                      <div class="absolute bottom-0 left-0 right-0 px-0.5 py-0 text-[6px] truncate" style="background:color-mix(in srgb, var(--bg-canvas) 70%, transparent);color:var(--text-secondary)">段{{ si+1 }}</div>
                    </div>
                  </div>
                </div>
                <div v-if="!allProjectImages.length" class="text-[9px] text-center py-2" style="color:var(--text-tertiary)">暂无图片，先生成资产或故事板</div>
              </div>
            </div>
            <!-- Prompt显示（始终可见，可展开） -->
            <div v-if="getVideoPrompt(videoLightbox)" class="mb-2">
              <div class="text-[9px] font-medium mb-0.5" style="color:var(--text-muted)">Prompt</div>
              <div class="px-2 py-1.5 rounded text-[10px] cursor-pointer prompt-display-box"
                   :class="{'line-clamp-2': !expandedVideoPrompt[videoLightbox]}"
                   style="color:var(--text-secondary)"
                   @click="toggleVideoPromptExpand(videoLightbox)">
                {{ getVideoPrompt(videoLightbox) }}
              </div>
              <button @click="toggleVideoPromptExpand(videoLightbox)" class="text-[8px] mt-0.5" style="color:var(--accent)">
                {{ expandedVideoPrompt[videoLightbox] ? '收起' : '展开全部' }}
              </button>
            </div>
            <!-- Prompt编辑区 -->
            <div class="space-y-1">
              <textarea v-model="videoPromptEdits[videoLightbox]" class="w-full rounded px-2 py-1 text-[10px] focus:outline-none resize-none prompt-edit-input" rows="3" :placeholder="getVideoPrompt(videoLightbox)||'输入自定义prompt...'"></textarea>
              <div class="flex justify-end gap-1">
                <button @click="videoLightbox=-1" class="px-2 py-0.5 text-[9px]" style="color:var(--text-muted)">关闭</button>
                <button v-if="getVideoUrl(videoLightbox)" @click="downloadVideo(videoLightbox)" class="px-2 py-0.5 rounded text-[9px]" style="background:var(--bg-surface-3);color:var(--text-secondary)">下载</button>
                <button @click="generateSingleVideo(videoLightbox)" class="px-2 py-0.5 rounded text-[9px]" style="background:var(--bg-surface-3);color:var(--text-secondary)" :disabled="isVideoGenerating(videoLightbox)||generatingVideo">重新生成</button>
                <button @click="generateSingleVideo(videoLightbox, videoPromptEdits[videoLightbox], selectedRefImages)" class="px-2 py-0.5 rounded text-[9px] font-medium" style="background:var(--accent);color:var(--text-primary)" :disabled="isVideoGenerating(videoLightbox)||generatingVideo">用此prompt生成</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ─── Agent面板（右下角浮动） ─── -->
      <!-- 迷你模式 -->
      <div v-if="showAgent && agentMini" @click="agentMini=false" class="fixed bottom-4 right-4 z-50 w-10 h-10 rounded-full flex items-center justify-center cursor-pointer shadow-2xl agent-mini-btn">
        <div class="w-6 h-6 rounded-full flex items-center justify-center" style="background: var(--accent)">
          <svg class="w-3 h-3" style="color: var(--text-primary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
        </div>
      </div>
      <!-- 完整模式 -->
      <div v-if="showAgent && !agentMini" class="fixed bottom-4 right-4 z-50 flex flex-col rounded-2xl shadow-2xl agent-panel">
        <div class="px-3 py-2 flex items-center justify-between shrink-0 rounded-t-2xl agent-header">
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 rounded-full flex items-center justify-center" style="background: var(--accent)">
              <svg class="w-2.5 h-2.5" style="color: var(--text-primary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            </div>
            <span class="text-[12px] font-semibold" style="color:var(--text-primary)">锤子导演</span>
            <span class="text-[9px]" style="color: var(--accent)">AI Agent</span>
          </div>
          <div class="flex items-center gap-2">
            <button @click="chatHistory=[]" class="text-[10px] transition" style="color:var(--text-tertiary)">清空</button>
            <button @click="agentMini=true" class="text-[10px] transition" style="color:var(--text-tertiary)">—</button>
            <button @click="showAgent=false" class="text-[10px] transition" style="color:var(--text-tertiary)">✕</button>
          </div>
        </div>
        <!-- Chat Messages -->
        <div ref="chatBox" class="flex-1 overflow-y-auto p-3 space-y-2">
          <div v-if="chatHistory.length === 0" class="text-center py-6">
            <div class="w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center" style="background: var(--accent-subtle)">
              <svg class="w-4 h-4" style="color: var(--accent)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            </div>
            <p class="text-[12px] mb-1" style="color:var(--text-secondary)">和锤子导演聊你的剧本</p>
            <p class="text-[10px]" style="color:var(--text-tertiary)">粘贴剧本让它拆段，或让它改分镜、加角色</p>
            <div class="mt-3 space-y-1.5">
              <button v-for="q in quickPrompts" :key="q" @click="chatInput=q;sendChat()" class="block w-full text-left px-3 py-2 rounded-lg text-[12px] transition agent-quick-btn" style="color:var(--text-muted)">
                {{ q }}
              </button>
            </div>
          </div>
          <div v-for="(msg, i) in chatHistory" :key="'m'+i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
            <div class="max-w-[85%] rounded-xl px-3 py-2 text-[12px] leading-relaxed"
              :style="msg.role === 'user' ? { background: 'var(--accent-glow)', color: 'var(--text-primary)' } : { background: 'var(--bg-surface-3)', color: 'var(--text-secondary)' }">
              <div v-if="msg.role === 'assistant' && msg.actions?.length" class="mb-1 flex gap-1 flex-wrap">
                <span v-for="a in msg.actions" :key="a" class="text-[8px] px-1.5 py-0.5 rounded-full" style="background:color-mix(in srgb, var(--color-success) 10%, transparent);color:var(--color-success)">{{ a }}</span>
              </div>
              <div class="whitespace-pre-wrap">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="chatLoading" class="flex justify-start">
            <div class="rounded-xl px-3 py-2 flex items-center gap-1.5" style="background:var(--bg-surface-3)">
              <div class="flex gap-0.5"><span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:var(--accent);opacity:0.6;animation-delay:0ms"></span><span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:var(--accent);opacity:0.6;animation-delay:150ms"></span><span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:var(--accent);opacity:0.6;animation-delay:300ms"></span></div>
              <span class="text-[11px]" style="color:var(--text-muted)">思考中...</span>
            </div>
          </div>
        </div>
        <!-- Chat Input -->
        <div class="p-3 agent-input-area">
          <div class="flex items-center gap-2 rounded-lg px-3 py-1.5 agent-input-box">
            <input v-model="chatInput" @keydown.enter="sendChat" class="flex-1 bg-transparent text-[13px] placeholder-white/40 outline-none" style="color:var(--text-primary)" placeholder="输入消息..." :disabled="chatLoading" />
            <button @click="sendChat" :disabled="chatLoading || !chatInput.trim()" class="shrink-0 w-8 h-8 flex items-center justify-center rounded-md disabled:opacity-30 transition agent-send-btn">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ═══ 剧本弹窗 ═══ -->
  <div v-if="scriptModal" class="fixed inset-0 flex items-center justify-center z-50" style="background:color-mix(in srgb, var(--bg-canvas) 50%, transparent)" @click.self="scriptModal=false">
    <div class="rounded-2xl p-5 w-full max-w-2xl" style="background:var(--bg-surface-1)">
      <div class="flex items-center justify-between mb-3">
        <span class="text-sm font-semibold" style="color:var(--text-primary)">剧本</span>
        <button @click="scriptModal=false" class="text-xs transition" style="color:var(--text-muted)">x</button>
      </div>
      <textarea v-model="rawScript" class="w-full rounded-lg px-3 py-2 text-xs focus:outline-none resize-none script-textarea" rows="10" placeholder="粘贴剧本..."></textarea>
      <div class="flex items-center gap-2 mt-3">
        <label class="px-3 py-1.5 rounded-lg text-xs cursor-pointer transition" style="background:var(--bg-surface-3);color:var(--text-secondary)">
          上传txt
          <input type="file" accept=".txt,.md,.text" class="hidden" @change="uploadScriptDetail" />
        </label>
        <div class="flex-1"></div>
        <button @click="saveRawScript(); scriptModal=false" class="px-3 py-1.5 rounded-lg text-xs transition" style="background:var(--bg-surface-3);color:var(--text-secondary)" :disabled="!rawScript.trim()">保存</button>
        <button @click="aiSplit(); scriptModal=false" class="px-3 py-1.5 rounded-lg text-xs font-medium transition" style="background:var(--accent);color:var(--text-primary)" :disabled="aiSplitting">{{ aiSplitting ? '拆段中...' : 'AI拆段' }}</button>
      </div>
    </div>
  </div>

  <!-- ═══ 视频播放弹窗 ═══ -->
  <div v-if="playingVideoUrl" class="fixed inset-0 flex items-center justify-center z-50 p-8" style="background:color-mix(in srgb, var(--bg-canvas) 80%, transparent)" @click.self="playingVideoUrl=''">
    <video :src="playingVideoUrl" class="max-w-full max-h-full rounded-lg" controls autoplay></video>
  </div>

  <!-- ═══ Prompt详情弹窗 ═══ -->
  <div v-if="promptDetailText" class="fixed inset-0 flex items-center justify-center z-50 p-4" style="background:color-mix(in srgb, var(--bg-canvas) 60%, transparent)" @click.self="promptDetailText=''">
    <div class="rounded-2xl p-5 w-full max-w-lg max-h-[60vh] overflow-y-auto" style="background:var(--bg-surface-2)">
      <div class="flex items-center justify-between mb-3">
        <span class="text-xs font-semibold" style="color:var(--text-primary)">Prompt详情</span>
        <button @click="promptDetailText=''" class="transition" style="color:var(--text-muted)">x</button>
      </div>
      <pre class="text-[11px] whitespace-pre-wrap break-words" style="color:var(--text-secondary)">{{ promptDetailText }}</pre>
    </div>
  </div>

  <!-- ═══ 图片预览浮层 ═══ -->
  <div v-if="previewImg" class="fixed z-[9999] pointer-events-none" :style="{left: previewPos.x+'px', top: previewPos.y+'px'}">
    <img :src="getUrl(previewImg)" class="max-w-[55vw] max-h-[70vh] object-contain rounded-lg shadow-2xl bg-black/90" style="border:1px solid var(--border-hairline)" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onActivated, onDeactivated, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { get, post, del, put } from '@/api'

const auth = useAuthStore()
const projects = ref<any[]>([])
const loading = ref(true)
const showCreate = ref(false)
const creating = ref(false)
const savingScript = ref(false)
const proj = ref<any>(null)
const showAgent = ref(true)
const agentMini = ref(false)
const assetCollapsed = ref(false)
const editAssets = ref<any[]>([])
const editSegments = ref<any[]>([])
const rawScript = ref('')
const scriptModal = ref(false)
const aiSplitting = ref(false)
const chatHistory = ref<{role:string,content:string,actions?:string[]}[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatBox = ref<HTMLElement|null>(null)
const assetFileInputs = ref<Record<number, any>>({})
const editingVideoPrompt = ref(-1)
const expandedAsset = ref(-1)
const videoPromptEdits = ref<Record<number, string>>({})
const promptDetailText = ref('')
const playingVideoUrl = ref('')
const saveNotification = ref('')
// ── 新增：视频灯箱 ──
const videoLightbox = ref(-1)
const isPortrait = computed(() => proj.value?.ratio?.includes('9:16'))
const showRefPicker = ref(false)
const selectedRefImages = ref<string[]>([])
const allProjectImages = computed(() => {
  const imgs: string[] = []
  editAssets.value.forEach((_, i) => { const u = getAssetResultImage(i); if (u) imgs.push(u) })
  editSegments.value.forEach((_, i) => { const u = getSegStoryboardImage(i); if (u) imgs.push(u) })
  return imgs
})
function toggleRefImage(url: string) {
  const idx = selectedRefImages.value.indexOf(url)
  if (idx >= 0) selectedRefImages.value.splice(idx, 1)
  else if (selectedRefImages.value.length < 3) selectedRefImages.value.push(url)
}
function openVideoLightbox(si: number) {
  videoLightbox.value = si
  selectedRefImages.value = []
  showRefPicker.value = false
}
// ── 新增：资产prompt编辑 ──
const editingAssetPrompt = ref(-1)
const assetPromptEdits = ref<Record<number, string>>({})
// ── 新增：故事板prompt编辑 ──
const editingStoryboardPrompt = ref(-1)
const storyboardPromptEdits = ref<Record<number, string>>({})
// ── 新增：视频prompt展开 ──
const expandedVideoPrompt = ref<Record<number, boolean>>({})
let pollTimer: any = null
// 生成锁，防止重复点击
const generatingAsset = ref(false)
const generatingAllAssets = ref(false)
const generatingVideo = ref(false)
const generatingAllVideos = ref(false)
const generatingStoryboard = ref(false)
const generatingAllStoryboards = ref(false)

// ── 图片预览浮层 ──
const previewImg = ref('')
const previewPos = ref({x:0, y:0})

function showPreview(url: string, e: MouseEvent) {
  if (!url) return
  previewImg.value = url
  const maxW = window.innerWidth * 0.55
  const maxH = window.innerHeight * 0.7
  const x = Math.min(e.clientX + 20, window.innerWidth - maxW - 20)
  const y = Math.min(e.clientY + 20, window.innerHeight - maxH - 20)
  previewPos.value = {x: Math.max(10, x), y: Math.max(10, y)}
}
function hidePreview() {
  previewImg.value = ''
}

const quickPrompts = [
  '帮我拆段这个剧本',
  '给第一个段加一个特写镜头',
  '把运镜改成更有电影感的',
  '帮我加一个反派角色',
]

const createForm = ref({ name:'', video_model:'Gemini Omni', image_model:'GPT-Image2', ratio:'16:9', resolution:'720p', image_resolution:'1K', duration:10, raw_script:'' })

// ── Computed ──

const videoDoneCount = computed(() => {
  if (!editSegments.value.length) return 0
  let count = 0
  for (let i = 0; i < editSegments.value.length; i++) {
    if (getVideoStatus(i) === 'completed') count++
  }
  return count
})

const workflowSteps = computed(() => {
  const p = proj.value
  if (!p) return []
  // Step 1: 剧本 → done when raw_script exists AND segments.length > 0
  const step1Done = !!(p.raw_script && p.segments?.length > 0)
  const step1Running = aiSplitting.value
  // Step 2: 资产生图 → done when all assets have phase2 results with status=completed
  const assets = p.assets || []
  const phase2 = p.results?.phase2 || []
  const step2Done = assets.length > 0 && phase2.length >= assets.length && phase2.every((x: any) => x.status === 'completed')
  const step2Running = phase2.some((x: any) => x.status === 'running')
  // Step 3: 故事板 → done when all segments have phase3 results with status=completed
  const segs = p.segments || []
  const phase3 = p.results?.phase3 || []
  const step3Done = segs.length > 0 && phase3.length >= segs.length && phase3.every((x: any) => x.status === 'completed')
  const step3Running = phase3.some((x: any) => x.status === 'running')
  // Step 4: 视频 → done when all segments have phase4 results with status=completed
  const phase4 = p.results?.phase4 || []
  const step4Done = segs.length > 0 && phase4.length >= segs.length && phase4.every((x: any) => x.status === 'completed')
  const step4Running = phase4.some((x: any) => x.status === 'running')

  return [
    { label: '剧本', status: step1Done ? 'done' : step1Running ? 'running' : 'pending', action: step1Done ? '' : 'AI拆段', actionFn: () => { scriptModal.value = true }, actionDisabled: aiSplitting.value },
    { label: '资产生图', status: step2Done ? 'done' : step2Running ? 'running' : 'pending', action: step2Done ? '' : '全部生成', actionFn: generateAllAssets, actionDisabled: generatingAllAssets.value },
    { label: '故事板', status: step3Done ? 'done' : step3Running ? 'running' : 'pending', action: step3Done ? '' : '全部生图', actionFn: generateAllStoryboards, actionDisabled: generatingAllStoryboards.value },
    { label: '视频', status: step4Done ? 'done' : step4Running ? 'running' : 'pending', action: step4Done ? '' : '全部生成', actionFn: generateAllVideos, actionDisabled: generatingAllVideos.value },
  ]
})

// ── Helper functions ──

function phaseLabel(p:number){return['未开始','AI拆段','资产生图','故事板生图','视频生成'][p]||'未开始'}
function phaseClass(p:number){if(p===0)return'bg-[var(--bg-surface-3)] text-[var(--text-tertiary)]';if(p===4)return'phase-done';return'bg-[var(--accent-subtle)] text-[var(--accent)]'}
function phaseBorderClass(p:number){const r=proj.value?.results?.[`phase${p}`]||[];if(r.some((x:any)=>x.status==='running'))return'bg-[var(--accent-subtle)]';if(r.length>0&&r.every((x:any)=>['completed','failed','timeout'].includes(x.status)))return'phase-done-border';return'bg-[var(--bg-surface-2)]'}
function canRunPhase(p:number){if(!proj.value)return false;const r=proj.value.results?.[`phase${p}`]||[];if(!r.length)return true;return r.some((x:any)=>!['completed','failed','timeout'].includes(x.status))}
function isPhaseRunning(p:number){if(!proj.value)return false;return(proj.value.results?.[`phase${p}`]||[]).some((x:any)=>x.status==='running')}
function isPhaseDone(p:number){if(!proj.value)return false;const r=proj.value.results?.[`phase${p}`]||[];return r.length>0&&r.every((x:any)=>['completed','failed','timeout'].includes(x.status))}
function getUrl(url:string){if(!url)return'';const t=localStorage.getItem('aiforge_token');if(url.startsWith('/api/')){const s=url.includes('?')?'&':'?';return t?`${url}${s}token=${t}`:url}return url}
function addShot(seg:any){if(!seg.shots)seg.shots=[];seg.shots.push({visual:'',camera:'',dialogue:'',lighting:'',audio:'',transition:'cut'})}
function addSegment(){editSegments.value.push({title:'',shots:[{visual:'',camera:'',dialogue:'',lighting:'',audio:'',transition:'cut'}],_open:true,assets:[]})}
function addAsset(){editAssets.value.push({name:'',type:'角色',prompt:'',reference_image:'',is_primary:true,reference_form:''})}
function getPrimaryCharacters(excludeIndex:number){return editAssets.value.filter((a:any,i:number)=>i!==excludeIndex&&a.type==='角色'&&a.is_primary!==false)}
function parseRefImages(ref:any):string[]{if(!ref)return[];if(Array.isArray(ref))return ref;try{return JSON.parse(ref)}catch{return[]}}
function showPromptDetail(text:string){promptDetailText.value=text}
function playVideo(si:number){playingVideoUrl.value=getUrl(getVideoUrl(si))}

// ── Asset functions ──

function getAssetImage(i:number):string{if(!proj.value?.results?.phase2?.[i]?.result_url)return'';return proj.value.results.phase2[i].result_url}
function getAssetResultImage(i:number):string{return proj.value?.results?.phase2?.[i]?.result_url||''}
function getAssetPrompt(i:number):string{return proj.value?.results?.phase2?.[i]?.prompt||''}
function isAssetGenerating(i:number):boolean{return proj.value?.results?.phase2?.[i]?.status==='running'}

function handleAssetImageClick(i:number){
  const a = editAssets.value[i]
  if(a?.reference_image || getAssetResultImage(i)) return
  uploadAssetRef(i)
}

async function generateSingleAsset(i:number){
  if(!proj.value||generatingAsset.value)return
  generatingAsset.value=true
  try{
    await post(`/project/${proj.value.id}/asset/${i}/generate`,{})
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingAsset.value=false
}

async function generateAllAssets(){
  if(!proj.value||generatingAllAssets.value)return
  generatingAllAssets.value=true
  for(let i=0;i<editAssets.value.length;i++){
    if(!isAssetGenerating(i)&&!getAssetResultImage(i)){
      try{await post(`/project/${proj.value.id}/asset/${i}/generate`,{})}catch(e:any){console.error(e)}
    }
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllAssets.value=false
}

function uploadAssetRef(i:number){
  const el=assetFileInputs.value[i] as HTMLInputElement|null
  el?.click()
}

async function handleAssetRefUpload(e:Event,i:number){
  const file=(e.target as HTMLInputElement).files?.[0]
  if(!file)return
  try{
    const formData=new FormData()
    formData.append('file',file)
    const res:any=await post('/gen/upload',formData)
    if(res.url){
      await post(`/project/${proj.value!.id}/asset/${i}/reference`,{image_url:res.url})
      editAssets.value[i].reference_image=res.url
      proj.value=await get(`/project/${proj.value!.id}`)
    }
  }catch(e:any){alert(e.message||'上传失败')}
}

function uploadAssetResult(i:number){
  const input=document.createElement('input')
  input.type='file'
  input.accept='image/*'
  input.onchange=async(e:Event)=>{
    const file=(e.target as HTMLInputElement).files?.[0]
    if(!file)return
    try{
      const formData=new FormData()
      formData.append('file',file)
      const res:any=await post('/gen/upload',formData)
      if(res.url){
        await post(`/project/${proj.value!.id}/asset/${i}/upload-result`,{image_url:res.url})
        proj.value=await get(`/project/${proj.value!.id}`)
      }
    }catch(e2:any){alert(e2.message||'上传失败')}
  }
  input.click()
}

// ── Storyboard functions ──

function getSegStoryboardImage(i:number):string{return proj.value?.results?.phase3?.[i]?.result_url||''}
function isSegStoryboardGenerating(i:number):boolean{return proj.value?.results?.phase3?.[i]?.status==='running'}
function getSegStoryboardStatus(i:number):string{return proj.value?.results?.phase3?.[i]?.status||''}

async function generateSingleStoryboard(i:number){
  if(!proj.value||generatingStoryboard.value)return
  generatingStoryboard.value=true
  try{
    await post(`/project/${proj.value.id}/segment/${i}/generate-storyboard`,{})
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingStoryboard.value=false
}

async function generateAllStoryboards(){
  if(!proj.value||generatingAllStoryboards.value)return
  generatingAllStoryboards.value=true
  for(let i=0;i<editSegments.value.length;i++){
    if(!isSegStoryboardGenerating(i)&&!getSegStoryboardImage(i)){
      try{await post(`/project/${proj.value.id}/segment/${i}/generate-storyboard`,{})}catch(e:any){console.error(e)}
    }
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllStoryboards.value=false
}

// ── Video functions ──

function videoResults(){return proj.value?.results?.phase4||[]}
function getVideoUrl(i:number):string{return videoResults()[i]?.result_url||''}
function getVideoStatus(i:number):string{return videoResults()[i]?.status||''}
function getVideoPrompt(i:number):string{return videoResults()[i]?.prompt||''}
function isVideoGenerating(i:number):boolean{return videoResults()[i]?.status==='running'}
function getSegRefImages(i:number):string[]{
  const ref=videoResults()[i]?.reference_images
  if(!ref)return[]
  try{return JSON.parse(ref)}catch{return[]}
}

async function generateSingleVideo(i:number,customPrompt?:string,refImages?:string[]){
  if(!proj.value||generatingVideo.value)return
  generatingVideo.value=true
  try{
    await post(`/project/${proj.value.id}/segment/${i}/generate-video`,{prompt:customPrompt||null, reference_images:refImages&&refImages.length?refImages:null})
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingVideo.value=false
}

async function generateAllVideos(){
  if(!proj.value||generatingAllVideos.value)return
  generatingAllVideos.value=true
  for(let i=0;i<editSegments.value.length;i++){
    if(!isVideoGenerating(i)&&getVideoStatus(i)!=='completed'){
      try{await post(`/project/${proj.value.id}/segment/${i}/generate-video`,{})}catch(e:any){console.error(e)}
    }
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllVideos.value=false
}

async function regenerateAllVideos(){
  if(!proj.value||generatingAllVideos.value)return
  if(!confirm('确定重新生成所有视频？将消耗积分'))return
  generatingAllVideos.value=true
  for(let i=0;i<editSegments.value.length;i++){
    try{await post(`/project/${proj.value.id}/segment/${i}/generate-video`,{})}catch(e:any){console.error(e)}
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllVideos.value=false
}

function toggleVideoPromptEdit(i:number){
  if(editingVideoPrompt.value===i){
    editingVideoPrompt.value=-1
  }else{
    editingVideoPrompt.value=i
    videoPromptEdits.value[i]=getVideoPrompt(i)||''
  }
}

// ── 资产prompt编辑函数 ──
function toggleAssetPromptEdit(i:number){
  if(editingAssetPrompt.value===i){
    editingAssetPrompt.value=-1
  }else{
    editingAssetPrompt.value=i
    assetPromptEdits.value[i]=getAssetPrompt(i)||''
  }
}
async function saveAssetPromptAndRegenerate(i:number){
  if(!proj.value)return
  const newPrompt=assetPromptEdits.value[i]
  if(newPrompt===undefined)return
  try{
    await post(`/project/${proj.value.id}/asset/${i}/generate`,{prompt:newPrompt})
    editingAssetPrompt.value=-1
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
}

// ── 故事板prompt编辑函数 ──
function getStoryboardPrompt(i:number):string{return proj.value?.results?.phase3?.[i]?.prompt||''}
function toggleStoryboardPromptEdit(i:number){
  if(editingStoryboardPrompt.value===i){
    editingStoryboardPrompt.value=-1
  }else{
    editingStoryboardPrompt.value=i
    storyboardPromptEdits.value[i]=getStoryboardPrompt(i)||''
  }
}
async function saveStoryboardPromptAndRegenerate(i:number){
  if(!proj.value||generatingStoryboard.value)return
  const newPrompt=storyboardPromptEdits.value[i]
  if(newPrompt===undefined)return
  generatingStoryboard.value=true
  try{
    await post(`/project/${proj.value.id}/segment/${i}/generate-storyboard`,{prompt:newPrompt})
    editingStoryboardPrompt.value=-1
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingStoryboard.value=false
}

// ── 视频prompt展开函数 ──
function toggleVideoPromptExpand(i:number){
  expandedVideoPrompt.value[i]=!expandedVideoPrompt.value[i]
}

function downloadVideo(si:number){
  if(!proj.value)return
  const url=getVideoUrl(si)
  if(!url)return
  window.open(getUrl(url),'_blank')
}

// ── Project CRUD ──

async function fetchProjects(){loading.value=true;try{projects.value=await get('/project/list')}catch(e){console.error(e)};loading.value=false}

async function createProject(){creating.value=true;try{const res:any=await post('/project/create',{...createForm.value,script:JSON.stringify({assets:[],segments:[]})});showCreate.value=false;const newRawScript=createForm.value.raw_script;createForm.value={name:'',video_model:'Gemini Omni',image_model:'GPT-Image2',ratio:'16:9',resolution:'720p',image_resolution:'1K',duration:10,raw_script:''};await fetchProjects();editAssets.value=[];editSegments.value=[];chatHistory.value=[];const newId=res?.id;if(newId){await openProject({id:newId})}else if(projects.value.length){await openProject(projects.value[0])}if(newRawScript.trim()){rawScript.value=newRawScript;scriptModal.value=true}}catch(e:any){alert(e.message||'创建失败')};creating.value=false}

function uploadScript(e:Event){const f=(e.target as HTMLInputElement).files?.[0];if(!f)return;const r=new FileReader();r.onload=()=>{createForm.value.raw_script=r.result as string};r.readAsText(f)}
function uploadScriptDetail(e:Event){const f=(e.target as HTMLInputElement).files?.[0];if(!f)return;const r=new FileReader();r.onload=()=>{rawScript.value=r.result as string};r.readAsText(f)}

async function saveRawScript(){if(!proj.value||!rawScript.value.trim())return;try{await put(`/project/${proj.value.id}/raw-script`,{raw_script:rawScript.value});proj.value=await get(`/project/${proj.value.id}`)}catch(e:any){alert(e.message||'保存失败')}}

async function openProject(p:any){try{proj.value=await get(`/project/${p.id}`);editAssets.value=proj.value.assets?.length?JSON.parse(JSON.stringify(proj.value.assets)).map((a:any)=>({...a,is_primary:a.type==='角色'?(a.is_primary!==false):undefined,reference_form:a.type==='角色'?(a.reference_form||''):undefined})):[];editSegments.value=proj.value.segments?.length?JSON.parse(JSON.stringify(proj.value.segments)).map((s:any)=>({...s,_open:false,assets:s.assets||s.referenced_assets||[]})):[];rawScript.value=proj.value.raw_script||'';scriptModal.value=false;try{const chatRes:any=await get(`/project/${p.id}/chat-history`);chatHistory.value=chatRes.history||[]}catch{chatHistory.value=[]}startPolling()}catch(e){console.error(e)}}
function closeProject(){proj.value=null;stopPolling();editAssets.value=[];editSegments.value=[];chatHistory.value=[]}

function startPolling(){stopPolling();pollTimer=setInterval(async()=>{if(!proj.value){stopPolling();return}const r=proj.value.results||{};if(!['phase2','phase3','phase4'].some(k=>(r[k]||[]).some((x:any)=>x.status==='running'||x.status==='pending'))){stopPolling();return}try{proj.value=await get(`/project/${proj.value.id}`)}catch(e){console.error(e)}},5000)}
function stopPolling(){if(pollTimer){clearInterval(pollTimer);pollTimer=null}}

async function saveScript(){if(!proj.value)return;savingScript.value=true;try{const prevResults=proj.value.results||{};const prevPhase2Count=(prevResults.phase2||[]).filter((x:any)=>x.status==='completed').length;const prevPhase3Count=(prevResults.phase3||[]).filter((x:any)=>x.status==='completed').length;const prevPhase4Count=(prevResults.phase4||[]).filter((x:any)=>x.status==='completed').length;const d={assets:editAssets.value.map(a=>({name:a.name,type:a.type,prompt:a.prompt,reference_image:a.reference_image,is_primary:a.type==='角色'?a.is_primary:undefined,reference_form:a.type==='角色'&&!a.is_primary?a.reference_form:undefined})),segments:editSegments.value.map(s=>{const{_open,...rest}=s;return rest})};await put(`/project/${proj.value.id}/script`,{script:JSON.stringify(d)});proj.value=await get(`/project/${proj.value.id}`);await fetchProjects();const newResults=proj.value.results||{};const newPhase2Count=(newResults.phase2||[]).filter((x:any)=>x.status==='completed').length;const newPhase3Count=(newResults.phase3||[]).filter((x:any)=>x.status==='completed').length;const newPhase4Count=(newResults.phase4||[]).filter((x:any)=>x.status==='completed').length;const clearedAssets=prevPhase2Count-newPhase2Count;const clearedStoryboards=prevPhase3Count-newPhase3Count;const clearedVideos=prevPhase4Count-newPhase4Count;const parts=[];if(clearedAssets>0)parts.push(`${clearedAssets}个资产`);if(clearedStoryboards>0)parts.push(`${clearedStoryboards}个故事板`);if(clearedVideos>0)parts.push(`${clearedVideos}段视频`);if(parts.length>0){saveNotification.value=`已保存，${parts.join('和')}需要重新生成`;setTimeout(()=>{saveNotification.value=''},4000)}else{saveNotification.value='已保存';setTimeout(()=>{saveNotification.value=''},2000)}}catch(e:any){alert(e.message||'保存失败')};savingScript.value=false}

async function aiSplit(){if(!proj.value)return;aiSplitting.value=true;try{const res:any=await post(`/project/${proj.value.id}/ai-split`,{duration_per_segment:proj.value.duration||10});editAssets.value=res.assets||[];editSegments.value=(res.segments||[]).map((s:any)=>({...s,_open:false,assets:s.assets||s.referenced_assets||[]}));proj.value=await get(`/project/${proj.value.id}`);await fetchProjects();await auth.fetchProfile();chatHistory.value.push({role:'assistant',content:`已拆段完成：${res.assets_count}个资产，${res.segments_count}段分镜。你可以在「资产」区查看和调整。`,actions:['update_script']})}catch(e:any){alert(e.message||'AI拆段失败')};aiSplitting.value=false}

async function sendChat(){if(!proj.value||!chatInput.value.trim()||chatLoading.value)return;const msg=chatInput.value;chatInput.value='';chatHistory.value.push({role:'user',content:msg});chatLoading.value=true;await nextTick();scrollChat();try{const res:any=await post(`/project/${proj.value.id}/chat`,{message:msg,history:chatHistory.value.slice(-20).map(m=>({role:m.role,content:m.content}))});const toolNames=res.tool_results?.length?res.tool_results.map((t:any)=>t.tool):[];chatHistory.value.push({role:'assistant',content:res.reply,actions:toolNames.length?toolNames:undefined});if(res.script_modified){editAssets.value=res.assets||[];editSegments.value=(res.segments||[]).map((s:any)=>({...s,_open:false,assets:s.assets||s.referenced_assets||[]}));proj.value=await get(`/project/${proj.value.id}`);await fetchProjects()}await auth.fetchProfile()}catch(e:any){chatHistory.value.push({role:'assistant',content:`出错了: ${e.message||'未知错误'}`})}chatLoading.value=false;await nextTick();scrollChat()}
function scrollChat(){if(chatBox.value)chatBox.value.scrollTop=chatBox.value.scrollHeight}

async function runPhase(phase:number){if(!proj.value)return;try{await post(`/project/${proj.value.id}/run`,{phase});proj.value=await get(`/project/${proj.value.id}`);await fetchProjects();await auth.fetchProfile();startPolling()}catch(e:any){alert(e.message||'执行失败')}}
async function retryItem(phase:number,index:number){if(!proj.value)return;try{await post(`/project/${proj.value.id}/retry/${phase}/${index}`,{});proj.value=await get(`/project/${proj.value.id}`);await auth.fetchProfile();startPolling()}catch(e:any){alert(e.message||'重试失败')}}
function downloadPhase(phase:number){if(!proj.value)return;const t=localStorage.getItem('aiforge_token');const u=`/api/project/${proj.value.id}/download/${phase}${t?`?token=${t}`:''}`;const a=document.createElement('a');a.href=u;a.download='';document.body.appendChild(a);a.click();document.body.removeChild(a)}
async function confirmDeleteAsset(i:number){if(!confirm('确定删除该资产？'))return;try{await del(`/project/${proj.value.id}/asset/${i}`);editAssets.value.splice(i,1);proj.value=await get(`/project/${proj.value.id}`)}catch(e:any){alert(e.message||'删除失败')}}
async function confirmDeleteSegment(si:number){if(!confirm('确定删除该段分镜？'))return;try{await del(`/project/${proj.value.id}/segment/${si}`);editSegments.value.splice(si,1);proj.value=await get(`/project/${proj.value.id}`)}catch(e:any){alert(e.message||'删除失败')}}
function confirmDeleteShot(seg:any,shi:number){if(!confirm('确定删除该镜头？'))return;seg.shots.splice(shi,1)}
function confirmRunPhase(phase:number){const labels={2:'资产生图',3:'故事板生图',4:'生成视频'};if(!confirm(`确定执行「${labels[phase]||'Phase'+phase}」？将消耗积分`))return;runPhase(phase)}
async function deleteProject(){if(!proj.value||!confirm('确定删除？'))return;try{await del(`/project/${proj.value.id}`);proj.value=null;stopPolling();await fetchProjects()}catch(e){console.error(e)}}

onMounted(fetchProjects)
onActivated(() => { fetchProjects() })
onDeactivated(() => { stopPolling() })
onUnmounted(() => { stopPolling() })
</script>

<style scoped>
.lbl { display:block; font-size:11px; color:var(--text-secondary); margin-bottom:4px; }
.phase-done { background: color-mix(in srgb, var(--color-success) 15%, transparent); color: var(--color-success); }
.phase-done-border { background: color-mix(in srgb, var(--color-success) 2%, transparent); }
.stat-tag-accent { background: var(--accent-subtle); color: var(--accent); }
.stat-tag-success { background: color-mix(in srgb, var(--color-success) 10%, transparent); color: var(--color-success); }
.inp { width:100%; background:var(--bg-input); border:1px solid var(--border-hairline); border-radius:8px; padding:8px 12px; color:var(--text-primary); font-size:12px; outline:none; transition:border-color 0.15s; }
.inp:focus { border-color:var(--accent); }
.inp::placeholder { color:var(--text-tertiary); }
.sel { width:100%; background:var(--bg-input); border:1px solid var(--border-hairline); border-radius:8px; padding:8px 12px; color:var(--text-primary); font-size:12px; outline:none; transition:border-color 0.15s; }
.sel:focus { border-color:var(--accent); }

.dot-spin { width:12px; height:12px; border:1.5px solid var(--accent-glow); border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; }
.line-clamp-2 { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.writing-vertical { writing-mode:vertical-rl; }

/* Project card hover */
.project-card:hover { background:var(--bg-surface-3) !important; }

/* Asset item hover */
.asset-item:hover { background:var(--bg-surface-3) !important; }

/* Segment item */
.segment-item:hover { background:var(--bg-surface-2) !important; }

/* Video item (legacy, kept for compat) */
.video-item:hover { background:var(--bg-surface-2) !important; }

/* ── 视频网格 ── */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.video-card {
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  background: var(--bg-surface-2);
  border: 1px solid var(--border-hairline);
}
.video-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.video-card-thumb {
  position: relative;
  background: rgba(0,0,0,0.3);
  overflow: hidden;
}
.video-card-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.25);
  color: white;
  font-size: 24px;
  opacity: 0;
  transition: opacity 0.15s;
}
.video-card:hover .play-overlay {
  opacity: 1;
}
.loading-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.2);
}
.error-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.15);
  cursor: pointer;
}
.error-state:hover {
  background: rgba(0,0,0,0.3);
}
.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.1);
  cursor: pointer;
  transition: background 0.15s;
}
.empty-state:hover {
  background: rgba(0,0,0,0.2);
}
.video-card-title-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: white;
  font-size: 10px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.video-card-status {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
}
.status-done {
  background: color-mix(in srgb, var(--color-success) 80%, transparent);
  color: white;
}
.status-running {
  background: color-mix(in srgb, var(--accent) 80%, transparent);
  color: white;
  animation: pulse-status 1.5s ease-in-out infinite;
}
.status-failed {
  background: color-mix(in srgb, var(--color-error) 80%, transparent);
  color: white;
}
@keyframes pulse-status {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ── 视频灯箱 ── */
.video-lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--bg-canvas) 80%, transparent);
  padding: 24px;
}
.video-lightbox-content {
  position: relative;
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
  background: var(--bg-surface-1);
  border: 1px solid var(--border-hairline);
  box-shadow: 0 8px 40px rgba(0,0,0,0.5);
}
.lightbox-close {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.5);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.lightbox-close:hover {
  background: rgba(0,0,0,0.8);
}
.lightbox-player {
  display: flex;
  align-items: center;
  justify-content: center;
  background: black;
  min-height: 200px;
}
.lightbox-video {
  width: 100%;
  max-height: 50vh;
  display: block;
}
.lightbox-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}
.lightbox-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}
.lightbox-info {
  padding: 16px;
  overflow-y: auto;
  max-height: 40vh;
}

/* ── Prompt显示框 ── */
.prompt-display-box {
  background: var(--bg-surface-3);
  border: 1px solid var(--border-hairline);
  transition: border-color 0.15s;
}
.prompt-display-box:hover {
  border-color: var(--accent);
}
.prompt-mini-display:hover {
  background: var(--bg-surface-2) !important;
}

/* Shot input fields */
.shot-input {
  background:var(--bg-input);
  border:1px solid var(--border-hairline);
  color:var(--text-secondary);
}
.shot-input:focus {
  border-color:var(--accent);
}

/* Prompt edit textarea */
.prompt-edit-input {
  background:var(--bg-input);
  border:1px solid var(--border-hairline);
  color:var(--text-muted);
}
.prompt-edit-input:focus {
  border-color:var(--accent);
}

/* Script textarea */
.script-textarea {
  background:var(--bg-input);
  border:1px solid var(--border-hairline);
  color:var(--text-secondary);
}
.script-textarea:focus {
  border-color:var(--accent);
}

/* Agent panel styles */
.agent-mini-btn {
  background:var(--bg-surface-1);
  border:2px solid var(--accent);
  box-shadow:0 0 20px var(--accent-glow);
}
.agent-panel {
  width:360px;
  height:480px;
  background:var(--bg-surface-1);
  border:1px solid var(--accent);
  box-shadow:0 0 20px var(--accent-glow), 0 0 60px var(--accent-subtle);
}
.agent-header {
  background:linear-gradient(135deg, var(--accent-glow), var(--accent-subtle));
  border-bottom:1px solid var(--border-hairline);
}
.agent-quick-btn {
  background:var(--bg-surface-3);
  border:1px solid var(--border-hairline);
}
.agent-quick-btn:hover {
  color:var(--text-secondary) !important;
  background:var(--bg-surface-3);
}
.agent-input-area {
  border-top:1px solid var(--border-hairline);
}
.agent-input-box {
  background:var(--bg-surface-3) !important;
  border:2px solid var(--accent) !important;
  box-shadow:0 0 8px var(--accent-subtle);
}
.agent-send-btn {
  background:var(--accent) !important;
}

@keyframes spin {
  to { transform:rotate(360deg); }
}
</style>
